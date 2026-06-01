# src/claude/tool_executor.py
"""
Tool executor — updated for user-level permissions.

WHAT CHANGED FROM V1:
  - scan_sharepoint_site replaced with scan_user_onedrive
  - get_file_permissions now uses OneDrive item IDs (no site_id needed)
  - Added classify_file_sensitivity
  - save_finding unchanged

THE TOOL USE LOOP — reminder of how this works:

  1. Claude returns a tool_use block
  2. THIS FILE runs the actual Python function
  3. We return a tool_result block
  4. That result goes back to Claude
  5. Claude gives the final answer

  This file is the only place that calls real functions.
  Claude never calls functions directly — it asks us to run them.
"""

import logging
from typing import Any
import anthropic

logger = logging.getLogger(__name__)

# Keywords that suggest a file is sensitive
SENSITIVE_KEYWORDS = {
    "critical": [
        "password", "credential", "secret", "private key",
        "api key", "token", "certificate",
    ],
    "high": [
        "salary", "payroll", "hr", "personnel", "medical",
        "legal", "contract", "nda", "confidential",
        "budget", "financial", "revenue", "forecast",
    ],
    "medium": [
        "internal", "draft", "strategy", "roadmap",
        "customer", "client", "proposal",
    ],
}


class ToolExecutor:
    """
    Executes tools Claude requests.
    Bridges Claude's decisions and actual code.
    """

    def __init__(
        self,
        onedrive_scanner: Any,   # OneDriveScanner instance
        db_session: Any,          # PostgreSQL session
    ) -> None:
        self._scanner = onedrive_scanner
        self._db = db_session

    def execute(
        self,
        tool_name: str,
        tool_input: dict,
        tool_use_id: str,
    ) -> dict:
        """
        Run one tool call. Return a tool_result block for Claude.

        The tool_use_id MUST be preserved in the result.
        Claude uses it to match results to requests.
        """
        logger.info(
            "Executing tool",
            extra={
                "component": "ToolExecutor",
                "tool": tool_name,
                "tool_use_id": tool_use_id,
            }
        )

        try:
            if tool_name == "scan_user_onedrive":
                result = self._scan_user_onedrive(**tool_input)

            elif tool_name == "get_file_permissions":
                result = self._get_file_permissions(**tool_input)

            elif tool_name == "classify_file_sensitivity":
                result = self._classify_file_sensitivity(**tool_input)

            elif tool_name == "save_finding":
                result = self._save_finding(**tool_input)

            else:
                raise ValueError(f"Unknown tool requested: {tool_name}")

            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": str(result),
                "is_error": False,
            }

        except Exception as e:
            logger.error(
                "Tool execution failed",
                extra={
                    "component": "ToolExecutor",
                    "tool": tool_name,
                    "error": str(e),
                }
            )
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Error executing {tool_name}: {str(e)}",
                "is_error": True,
            }

    def execute_all(
        self,
        tool_calls: list[anthropic.types.ToolUseBlock],
    ) -> list[dict]:
        """
        Execute all tool calls from one Claude response.
        Returns all results as a list — sent back together.
        """
        return [
            self.execute(
                tool_name=call.name,
                tool_input=call.input,
                tool_use_id=call.id,
            )
            for call in tool_calls
        ]

    # ─────────────────────────────────────────
    # Tool implementations
    # ─────────────────────────────────────────

    def _scan_user_onedrive(
        self,
        include_subfolders: bool = True,
    ) -> dict:
        """Scan the user's OneDrive for risk findings."""
        findings = self._scanner.scan_user_onedrive()
        return {
            "findings": findings,
            "total_found": len(findings),
        }

    def _get_file_permissions(
        self,
        item_id: str,
    ) -> dict:
        """Get permissions for a specific OneDrive file."""
        if not item_id:
            raise ValueError("item_id cannot be empty")
        permissions = self._scanner.get_file_permissions(item_id)
        return {
            "item_id": item_id,
            "permissions": permissions,
            "count": len(permissions),
        }

    def _classify_file_sensitivity(
        self,
        file_name: str,
    ) -> dict:
        """
        Classify how sensitive a file is by its name.

        Checks file name against known sensitive keyword patterns.
        Returns sensitivity level and matching keywords found.
        """
        if not file_name:
            raise ValueError("file_name cannot be empty")

        name_lower = file_name.lower()
        matched_keywords: list[str] = []
        highest_level = "low"

        # Check from most critical downward
        for level in ["critical", "high", "medium"]:
            for keyword in SENSITIVE_KEYWORDS[level]:
                if keyword in name_lower:
                    matched_keywords.append(keyword)
                    if highest_level != "critical":
                        highest_level = level

        return {
            "file_name": file_name,
            "sensitivity_level": highest_level,
            "matched_keywords": matched_keywords,
            "is_sensitive": highest_level in ["critical", "high"],
        }

    def _save_finding(
        self,
        resource_id: str,
        resource_name: str,
        finding_type: str,
        severity: str,
        evidence: str,
    ) -> dict:
        """Save a verified finding to PostgreSQL."""
        finding_id = self._db.save_finding(
            resource_id=resource_id,
            resource_name=resource_name,
            finding_type=finding_type,
            severity=severity,
            evidence=evidence,
        )
        return {"finding_id": finding_id, "status": "saved"}