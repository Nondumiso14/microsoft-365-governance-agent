"""
Claude tool schemas — updated for user-level permissions.

WHAT CHANGED FROM V1:
  - scan_sharepoint_site replaced with scan_user_onedrive
    (SharePoint org-wide requires admin — OneDrive does not)
  - get_file_permissions updated to use OneDrive item IDs
  - save_finding unchanged — database layer is the same
  - Added classify_sensitivity tool — helps Claude identify
    sensitive files by name pattern without reading content

NAMING CONVENTION (repeat from v1 — important):
  Function:  scan_user_onedrive
  Schema:    scan_user_onedrive_schema
  Always paired. Always in the same file.
"""

from anthropic.types import ToolParam


# Tool 1: Scan the user's OneDrive


scan_user_onedrive_schema = ToolParam({
    "name": "scan_user_onedrive",
    "description": (
        "Scans the logged-in user's OneDrive to discover all files "
        "and their current sharing permissions. Use this tool when "
        "the Discovery Agent needs to build a complete list of files "
        "the user owns and identify which ones have risky sharing settings. "
        "Returns a list of risk findings — each finding includes the file "
        "name, the type of risk, and the evidence."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "include_subfolders": {
                "type": "boolean",
                "description": (
                    "Whether to scan files inside subfolders. "
                    "Defaults to True."
                ),
                "default": True,
            }
        },
        "required": [],
    }
})


# Tool 2: Get permissions for a specific file


get_file_permissions_schema = ToolParam({
    "name": "get_file_permissions",
    "description": (
        "Retrieves all sharing permissions for a specific file in "
        "the user's OneDrive. Use this when the Permission Analysis "
        "Agent needs to inspect a single file in detail. Returns a "
        "list of permission objects each showing who has access, "
        "what role they have, and whether the link is anonymous, "
        "organisation-wide, or granted to a specific user."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "item_id": {
                "type": "string",
                "description": (
                    "The Microsoft Graph item ID of the file. "
                    "Get this from the scan_user_onedrive results. "
                    "Must not be empty."
                )
            }
        },
        "required": ["item_id"],
    }
})


# Tool 3: Classify file sensitivity by name


classify_file_sensitivity_schema = ToolParam({
    "name": "classify_file_sensitivity",
    "description": (
        "Analyses a file name to determine how sensitive the file "
        "is likely to be, based on keywords in the name. Use this "
        "tool when the Sensitive Content Agent needs to score files "
        "before combining sensitivity with permission exposure to "
        "calculate overall risk. Returns a sensitivity level and "
        "the keywords that triggered the classification."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": (
                    "The full file name including extension. "
                    "Example: 'Project-Atlas-Budget-2025.xlsx'"
                )
            }
        },
        "required": ["file_name"],
    }
})

# Tool 4: Save finding to database


save_finding_schema = ToolParam({
    "name": "save_finding",
    "description": (
        "Saves a confirmed governance finding to the PostgreSQL database. "
        "Use this tool after the Policy Reasoning Agent has verified that "
        "a finding is valid and assigned it a severity score. The finding "
        "will be stored with a timestamp and matched against previous "
        "findings to detect recurring issues. "
        "Returns the database ID assigned to this finding."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "resource_id": {
                "type": "string",
                "description": "The Microsoft Graph item ID of the affected file."
            },
            "resource_name": {
                "type": "string",
                "description": "The human-readable file name."
            },
            "finding_type": {
                "type": "string",
                "description": "The category of risk found.",
                "enum": [
                    "anonymous_link",
                    "external_user_access",
                    "org_wide_link",
                    "stale_guest",
                    "sensitive_content_exposed",
                    "direct_grant",
                ]
            },
            "severity": {
                "type": "string",
                "description": "The risk severity level.",
                "enum": ["critical", "high", "medium", "low"]
            },
            "evidence": {
                "type": "string",
                "description": (
                    "Specific, detailed evidence for this finding. "
                    "Include the file name, the type of exposure, "
                    "and why it is considered risky."
                )
            }
        },
        "required": [
            "resource_id",
            "resource_name",
            "finding_type",
            "severity",
            "evidence",
        ],
    }
})


# Tool groups — import these in agent files


# Discovery Agent tools
DISCOVERY_TOOLS = [scan_user_onedrive_schema]

# Permission Analysis Agent tools
PERMISSION_TOOLS = [get_file_permissions_schema]

# Sensitive Content Agent tools
CONTENT_TOOLS = [classify_file_sensitivity_schema]

# Policy Reasoning Agent tools — needs to save findings
POLICY_TOOLS = [save_finding_schema]

# All tools — use only in the orchestrator
ALL_TOOLS = [
    scan_user_onedrive_schema,
    get_file_permissions_schema,
    classify_file_sensitivity_schema,
    save_finding_schema,
]