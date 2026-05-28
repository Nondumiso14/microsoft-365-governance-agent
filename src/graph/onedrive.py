# src/graph/onedrive.py
"""
OneDrive scanner — user's own files and permissions.

WHY ONEDRIVE INSTEAD OF SHAREPOINT FOR NOW:
  With user-level delegated permissions, we can fully scan
  the logged-in user's OneDrive without any admin approval.
  This gives us real data to work with immediately.

  SharePoint org-wide scanning comes back when IT grants
  admin consent. The code structure is identical — only the
  Graph endpoint changes.

WHAT YOU SHOULD HAVE TRIED YOURSELF:
  Before reading this — did you test these endpoints in Graph Explorer?
    GET /me/drive
    GET /me/drive/root/children
    GET /me/drive/items/{item-id}/permissions
  
  The JSON responses from those calls are what these models are built from.
  You should know what a real Graph response looks like before writing
  code that parses it.
"""

import logging
from src.graph.client import GraphClient
from src.models.graph_models import DriveItem, Permission

logger = logging.getLogger(__name__)


class OneDriveScanner:
    """
    Scans the logged-in user's OneDrive for files and permissions.
    """

    def __init__(self, graph_client: GraphClient) -> None:
        self._graph = graph_client

    def get_all_files(self) -> list[dict]:
        """
        Get every file in the user's OneDrive.

        Uses pagination to handle drives with many files.
        Returns a flat list of all files found.
        """
        logger.info(
            "Starting OneDrive file scan",
            extra={"component": "OneDriveScanner"}
        )

        files = self._graph.get_all_pages("/me/drive/root/children")

        logger.info(
            "OneDrive scan complete",
            extra={
                "component": "OneDriveScanner",
                "file_count": len(files),
            }
        )
        return files

    def get_file_permissions(self, item_id: str) -> list[dict]:
        """
        Get all sharing permissions for a specific file or folder.

        This is where we find:
          - Anonymous links (scope: "anonymous")
          - Organisation-wide links (scope: "organization")
          - External user access (grantedToV2.user with external email)
          - Direct user grants

        Args:
            item_id: The Graph item ID from get_all_files()
        """
        if not item_id:
            raise ValueError("item_id cannot be empty")

        data = self._graph.get(f"/me/drive/items/{item_id}/permissions")
        permissions = data.get("value", [])

        logger.info(
            "Permissions fetched",
            extra={
                "component": "OneDriveScanner",
                "item_id": item_id,
                "permission_count": len(permissions),
            }
        )
        return permissions

    def scan_for_risks(self) -> list[dict]:
        """
        Full scan — get all files then check permissions on each one.

        Returns a list of raw risk findings ready for Claude to analyse.

        This is the main method the Discovery Agent calls.
        """
        findings: list[dict] = []
        files = self.get_all_files()

        for file in files:
            item_id = file.get("id")
            file_name = file.get("name", "unknown")

            if not item_id:
                continue

            permissions = self.get_file_permissions(item_id)

            for perm in permissions:
                risk = self._classify_permission(
                    file_name=file_name,
                    item_id=item_id,
                    permission=perm,
                )
                if risk:
                    findings.append(risk)

        logger.info(
            "Risk scan complete",
            extra={
                "component": "OneDriveScanner",
                "files_scanned": len(files),
                "risks_found": len(findings),
            }
        )
        return findings

    def _classify_permission(
        self,
        file_name: str,
        item_id: str,
        permission: dict,
    ) -> dict | None:
        """
        Look at one permission entry and decide if it is risky.

        Returns a finding dict if risky, None if safe.

        WHAT THE PERMISSION OBJECT LOOKS LIKE (from Graph Explorer):
        {
          "id": "perm123",
          "roles": ["write"],
          "link": {
            "scope": "anonymous",
            "type": "edit"
          },
          "grantedToV2": {
            "user": {
              "email": "someone@external.com"
            }
          }
        }
        """
        link = permission.get("link", {})
        scope = link.get("scope", "")
        roles = permission.get("roles", [])
        granted_to = permission.get("grantedToV2", {})

        # Anonymous link — anyone on internet can access
        if scope == "anonymous":
            return {
                "resource_id": item_id,
                "resource_name": file_name,
                "finding_type": "anonymous_link",
                "severity": "critical" if "write" in roles else "high",
                "evidence": (
                    f"File '{file_name}' has an anonymous "
                    f"{'edit' if 'write' in roles else 'view'} link. "
                    f"Anyone with the link can access this file "
                    f"without logging in."
                ),
            }

        # Organisation-wide link
        if scope == "organization":
            return {
                "resource_id": item_id,
                "resource_name": file_name,
                "finding_type": "org_wide_link",
                "severity": "medium",
                "evidence": (
                    f"File '{file_name}' is shared with the entire "
                    f"organisation. Every employee can access it."
                ),
            }

        # External user access — check if email domain is external
        user = granted_to.get("user", {})
        email = user.get("email", "")
        if email and self._is_external_email(email):
            return {
                "resource_id": item_id,
                "resource_name": file_name,
                "finding_type": "external_user_access",
                "severity": "high",
                "evidence": (
                    f"File '{file_name}' is accessible to external "
                    f"user {email}."
                ),
            }

        # Safe — no risk detected
        return None

    def _is_external_email(self, email: str) -> bool:
        """
        Check if an email belongs to an external domain.

        In production this checks against the approved domains list
        stored in the database. For now we check if the domain
        does not match the configured tenant domain.
        """
        if not email or "@" not in email:
            return False
        domain = email.split("@")[1].lower()
        # Add your company domain here
        internal_domains = {"kion.co.za", "yourdomain.com"}
        return domain not in internal_domains