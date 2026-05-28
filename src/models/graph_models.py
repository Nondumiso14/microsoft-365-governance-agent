# src/models/graph_models.py
"""
Microsoft Graph API response models.

WHY THIS FILE EXISTS:
  Every time our Graph client gets data back from Microsoft,
  it comes as raw JSON. Pydantic models turn that raw JSON
  into proper Python objects with type safety.

  Without this: you access data like result["grantedToV2"]["user"]["email"]
  and if ANY key is missing Python crashes with a KeyError.

  With this: you access data like permission.granted_to.user.email
  and Pydantic handles missing fields gracefully using Optional.

WHERE THESE MODELS COME FROM:
  Every model here is built directly from the official Microsoft
  Graph API documentation and real Graph Explorer responses.
  Source: https://learn.microsoft.com/en-us/graph/api/resources/driveitem
  Source: https://learn.microsoft.com/en-us/graph/api/resources/permission

HOW PYDANTIC WORKS IN ONE SENTENCE:
  You define a class that describes the shape of your data.
  Pydantic reads the JSON, matches fields by name, and gives
  you a typed Python object. Any field marked Optional[x]
  will be None if Microsoft does not include it in the response.

SENIOR DEVELOPER NOTE ON NAMING:
  Microsoft Graph uses camelCase: "lastModifiedDateTime"
  Python convention is snake_case: "last_modified_date_time"
  We use Pydantic's Field(alias=...) to bridge the gap.
  This means we write Python-style names in our code but
  Pydantic maps them correctly from Microsoft's JSON.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# BUILDING BLOCK MODELS
# These are small models used INSIDE the bigger models below.
# Think of them as smaller Lego pieces that build bigger ones.
# ─────────────────────────────────────────────────────────────

class IdentityDetail(BaseModel):
    """
    Represents one identity — a user, app, or device.

    Real Graph response example:
    {
        "displayName": "Nondumiso Khumalo",
        "email": "nondumiso@kion.co.za",
        "id": "abc123"
    }
    """
    display_name: Optional[str] = Field(None, alias="displayName")
    email: Optional[str] = Field(None, alias="email")
    id: Optional[str] = Field(None, alias="id")

    model_config = {"populate_by_name": True}


class IdentitySet(BaseModel):
    """
    A set of identities — user, application, and/or device.

    Microsoft wraps identities in this container.
    In most cases we only care about the "user" field.

    Real Graph response example:
    {
        "user": {
            "displayName": "Nondumiso Khumalo",
            "email": "nondumiso@kion.co.za"
        }
    }
    """
    user: Optional[IdentityDetail] = None
    application: Optional[IdentityDetail] = None
    device: Optional[IdentityDetail] = None

    model_config = {"populate_by_name": True}


class SharingLink(BaseModel):
    """
    Represents a sharing link on a file.

    This is the most important model for detecting risks.

    scope tells us HOW WIDE the sharing is:
      "anonymous"    = anyone on the internet — CRITICAL risk
      "organization" = everyone in the company — HIGH risk
      "users"        = specific people only — check who

    type tells us WHAT they can do:
      "view"  = read only
      "edit"  = can make changes — more dangerous
      "embed" = can embed in a webpage

    Real Graph response example:
    {
        "scope": "anonymous",
        "type": "edit",
        "webUrl": "https://1drv.ms/x/s!abc123"
    }
    """
    scope: Optional[str] = None
    type: Optional[str] = None
    web_url: Optional[str] = Field(None, alias="webUrl")
    application: Optional[IdentityDetail] = None

    model_config = {"populate_by_name": True}


class GrantedToV2(BaseModel):
    """
    Who a direct permission has been granted to.

    Microsoft deprecated 'grantedTo' in favour of 'grantedToV2'.
    We use V2 as the docs recommend.

    Real Graph response example:
    {
        "user": {
            "displayName": "External Partner",
            "email": "partner@external.com",
            "id": "xyz789"
        }
    }
    """
    user: Optional[IdentityDetail] = None
    group: Optional[IdentityDetail] = None
    application: Optional[IdentityDetail] = None

    model_config = {"populate_by_name": True}


class FileFacet(BaseModel):
    """
    Present when the DriveItem is a file (not a folder).
    Contains MIME type information.

    Real Graph response example:
    {
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    """
    mime_type: Optional[str] = Field(None, alias="mimeType")

    model_config = {"populate_by_name": True}


class FolderFacet(BaseModel):
    """
    Present when the DriveItem is a folder (not a file).
    Contains child count.

    Real Graph response example:
    {
        "childCount": 12
    }
    """
    child_count: Optional[int] = Field(None, alias="childCount")

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────────────────────
# MAIN MODELS
# These are the models our agents and scanners actually use.
# ─────────────────────────────────────────────────────────────

class DriveItem(BaseModel):
    """
    Represents a file or folder in Microsoft OneDrive or SharePoint.

    This is the most used model in the whole project.
    Every file the scanner finds comes back as a DriveItem.

    HOW TO TELL IF IT IS A FILE OR FOLDER:
      If item.file is not None  → it is a file
      If item.folder is not None → it is a folder

    Real Graph response example from GET /me/drive/root/children:
    {
        "id": "01BYE5RZ6QN3ZWBTUBNZA3QHGJ2NXEEJKT",
        "name": "Project-Atlas-Budget-2025.xlsx",
        "size": 45231,
        "lastModifiedDateTime": "2025-05-01T10:30:00Z",
        "webUrl": "https://kion-my.sharepoint.com/...",
        "file": {
            "mimeType": "application/vnd.openxmlformats-..."
        },
        "createdBy": {
            "user": {
                "displayName": "Nondumiso Khumalo",
                "email": "nondumiso@kion.co.za"
            }
        }
    }
    """
    id: str
    name: str
    size: Optional[int] = None
    web_url: Optional[str] = Field(None, alias="webUrl")
    last_modified_datetime: Optional[datetime] = Field(
        None, alias="lastModifiedDateTime"
    )
    created_datetime: Optional[datetime] = Field(
        None, alias="createdDateTime"
    )
    created_by: Optional[IdentitySet] = Field(None, alias="createdBy")
    last_modified_by: Optional[IdentitySet] = Field(
        None, alias="lastModifiedBy"
    )

    # If file is not None — this DriveItem is a file
    file: Optional[FileFacet] = None

    # If folder is not None — this DriveItem is a folder
    folder: Optional[FolderFacet] = None

    # Convenience properties
    @property
    def is_file(self) -> bool:
        """Returns True if this item is a file."""
        return self.file is not None

    @property
    def is_folder(self) -> bool:
        """Returns True if this item is a folder."""
        return self.folder is not None

    @property
    def extension(self) -> str:
        """
        Returns the file extension in lowercase.
        Example: 'Budget.xlsx' → 'xlsx'
        Returns empty string if no extension.
        """
        if "." in self.name:
            return self.name.rsplit(".", 1)[-1].lower()
        return ""

    model_config = {"populate_by_name": True}


class Permission(BaseModel):
    """
    Represents one sharing permission on a file or folder.

    A single file can have MULTIPLE permissions.
    For example:
      - One anonymous link (anyone can view)
      - One direct grant to a specific external user
      - One org-wide link

    Our scanner checks EVERY permission on EVERY file.

    HOW TO READ A PERMISSION:

    If permission.link is not None:
      → This is a sharing link
      → Check permission.link.scope:
          "anonymous"    = CRITICAL — anyone on internet
          "organization" = HIGH — entire company
          "users"        = check who specifically

    If permission.granted_to_v2 is not None:
      → This is a direct grant to a specific person
      → Check permission.granted_to_v2.user.email
      → If the email domain is external = HIGH risk

    Real Graph response example from GET /me/drive/items/{id}/permissions:
    {
        "id": "perm-abc123",
        "roles": ["write"],
        "link": {
            "scope": "anonymous",
            "type": "edit",
            "webUrl": "https://1drv.ms/x/s!abc123"
        }
    }

    Another example — direct user grant:
    {
        "id": "perm-xyz789",
        "roles": ["read"],
        "grantedToV2": {
            "user": {
                "displayName": "External Partner",
                "email": "partner@external-company.com",
                "id": "ext-user-id"
            }
        }
    }
    """
    id: str
    roles: list[str] = Field(default_factory=list)

    # Present when this permission is a sharing link
    link: Optional[SharingLink] = None

    # Present when this permission is granted directly to a person
    # Microsoft deprecated grantedTo — use grantedToV2
    granted_to_v2: Optional[GrantedToV2] = Field(
        None, alias="grantedToV2"
    )

    # When this sharing link expires (if set)
    expiration_datetime: Optional[datetime] = Field(
        None, alias="expirationDateTime"
    )

    # Convenience properties for risk classification
    @property
    def is_anonymous_link(self) -> bool:
        """True if anyone on the internet can access this."""
        return (
            self.link is not None
            and self.link.scope == "anonymous"
        )

    @property
    def is_org_wide_link(self) -> bool:
        """True if everyone in the organisation can access this."""
        return (
            self.link is not None
            and self.link.scope == "organization"
        )

    @property
    def is_edit_permission(self) -> bool:
        """True if this permission allows writing/editing."""
        return "write" in self.roles or (
            self.link is not None and self.link.type == "edit"
        )

    @property
    def external_user_email(self) -> Optional[str]:
        """
        Returns the email if this is a direct grant to a user.
        Returns None if it is a link or no email available.
        """
        if self.granted_to_v2 and self.granted_to_v2.user:
            return self.granted_to_v2.user.email
        return None

    model_config = {"populate_by_name": True}


class DriveItemWithPermissions(BaseModel):
    """
    A DriveItem combined with its permissions list.

    This is what the scanner builds after fetching both.
    It is what gets passed to Claude for risk analysis.

    Usage:
        item = DriveItemWithPermissions(
            drive_item=some_file,
            permissions=[perm1, perm2]
        )
        # Then check:
        for perm in item.permissions:
            if perm.is_anonymous_link:
                # flag as critical risk
    """
    drive_item: DriveItem
    permissions: list[Permission] = Field(default_factory=list)

    @property
    def has_anonymous_link(self) -> bool:
        """True if ANY permission on this file is anonymous."""
        return any(p.is_anonymous_link for p in self.permissions)

    @property
    def has_org_wide_link(self) -> bool:
        """True if ANY permission is organisation-wide."""
        return any(p.is_org_wide_link for p in self.permissions)

    @property
    def external_users(self) -> list[str]:
        """
        Returns a list of external user emails who have direct access.
        Empty list if no external users.
        """
        emails = []
        for perm in self.permissions:
            email = perm.external_user_email
            if email:
                emails.append(email)
        return emails


class UserProfile(BaseModel):
    """
    The logged-in user's Microsoft profile.

    Returned by GET /me

    Real Graph response example:
    {
        "id": "user-object-id-abc123",
        "displayName": "Nondumiso Khumalo",
        "mail": "nondumiso@kion.co.za",
        "userPrincipalName": "nondumiso@kion.co.za",
        "jobTitle": "AI Engineer",
        "officeLocation": "Johannesburg"
    }
    """
    id: str
    display_name: Optional[str] = Field(None, alias="displayName")
    mail: Optional[str] = None
    user_principal_name: Optional[str] = Field(
        None, alias="userPrincipalName"
    )
    job_title: Optional[str] = Field(None, alias="jobTitle")
    office_location: Optional[str] = Field(None, alias="officeLocation")

    @property
    def email(self) -> Optional[str]:
        """
        Returns the user's email.
        Tries 'mail' first, falls back to 'userPrincipalName'.
        Both hold the email in most tenants.
        """
        return self.mail or self.user_principal_name

    @property
    def domain(self) -> Optional[str]:
        """
        Returns just the domain part of the email.
        Example: 'nondumiso@kion.co.za' → 'kion.co.za'
        """
        if self.email and "@" in self.email:
            return self.email.split("@")[1].lower()
        return None

    model_config = {"populate_by_name": True}


class GraphListResponse(BaseModel):
    """
    The wrapper Microsoft Graph puts around every list response.

    When you call GET /me/drive/root/children, the response is:
    {
        "@odata.context": "...",
        "@odata.nextLink": "https://graph.microsoft.com/v1.0/...",
        "value": [
            { DriveItem1 },
            { DriveItem2 },
            ...
        ]
    }

    The actual items are always in the "value" array.
    The "@odata.nextLink" is the URL for the next page — only
    present if there are more items than the page limit (200).

    Our GraphClient.get_all_pages() uses next_link to paginate.
    """
    value: list[dict] = Field(default_factory=list)
    next_link: Optional[str] = Field(None, alias="@odata.nextLink")
    context: Optional[str] = Field(None, alias="@odata.context")

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────────────────────
# RISK FINDING MODEL
# The output of our scanner — what gets saved to PostgreSQL
# and sent to Claude for analysis.
# ─────────────────────────────────────────────────────────────

class RawFinding(BaseModel):
    """
    A raw risk finding produced by the OneDrive scanner.

    This is the output of OneDriveScanner.scan_for_risks().
    It goes to Claude for policy reasoning and scoring.
    After Claude analyses it, it gets saved to PostgreSQL
    as a Finding record.

    Every field here maps directly to a column in the
    findings table in database.py.
    """
    resource_id: str
    resource_name: str
    finding_type: str
    severity: str
    evidence: str

    # Optional context — helps Claude reason about the risk
    file_extension: Optional[str] = None
    permission_scope: Optional[str] = None
    permission_roles: list[str] = Field(default_factory=list)
    external_email: Optional[str] = None