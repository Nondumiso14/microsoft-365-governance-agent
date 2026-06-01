# src/models/agent_models.py
"""
WHAT THIS FILE IS:
  Pydantic models that define the shape of data flowing
  BETWEEN agents in the pipeline.

WHY THIS EXISTS:
  When one agent finishes and hands results to the next,
  both agents need to agree on the exact format of that data.
  These models are that agreement — the shared contract.

BEGINNER TIP — WHAT IS PYDANTIC?
  Pydantic is a library that validates data automatically.
  You define what a piece of data SHOULD look like.
  Pydantic checks every value matches that definition.

  Without Pydantic: data["severity"] might be "Critical" or "critical"
  or "CRITICAL" — inconsistent, causes bugs.

  With Pydantic: severity is always validated against allowed values.

WHAT IMPORTS THIS:
  src/agents/orchestrator.py  → needs AgentState, ScanRequest
  src/agents/core_agents.py   → needs ScanRequest, AgentMessage
  src/agents/policy_agents.py → needs PolicyFinding
  src/agents/action_agents.py → needs RemediationAction

REFERENCES:
  graph_models.py → RawFinding is imported and used inside PolicyFinding
  risk_models.py  → RiskLevel enum is used in PolicyFinding
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """
    The possible states any agent can be in.

    WHY AN ENUM?
      An enum is a list of fixed allowed values.
      Without it: status could be "running", "Running", "RUNNING" — messy.
      With it: status is always one of these exact values.
    """
    PENDING = "pending"       # Not started yet
    RUNNING = "running"       # Currently working
    COMPLETE = "complete"     # Finished successfully
    FAILED = "failed"         # Something went wrong
    WAITING = "waiting"       # Waiting for human approval


class ScanRequest(BaseModel):
    """
    What the user asks the agent to do.

    FLOW:
      User types a request →
      Scope Agent reads this model →
      Decides what to scan based on it

    EXAMPLE:
      ScanRequest(
          user_request="Scan my OneDrive for oversharing risks",
          scan_type="onedrive",
          include_permissions=True
      )
    """
    user_request: str
    # The raw text of what the user asked for

    scan_type: str = "onedrive"
    # What to scan — "onedrive" for now, "sharepoint" later

    include_permissions: bool = True
    # Whether to check file permissions — almost always True

    include_sensitivity: bool = True
    # Whether to classify files by content sensitivity

    requested_at: datetime = Field(default_factory=datetime.utcnow)
    # When the request was made — auto-filled


class AgentMessage(BaseModel):
    """
    A message passed between agents.

    Think of agents like workers on a production line.
    Each worker completes their task and puts the result
    in a box (AgentMessage) and passes it to the next worker.

    FLOW:
      Discovery Agent completes →
      Puts results in AgentMessage →
      Permission Analysis Agent receives it →
      Reads the files list and starts checking permissions
    """
    from_agent: str
    # Which agent sent this message — e.g. "DiscoveryAgent"

    to_agent: str
    # Which agent should receive it — e.g. "PermissionAnalysisAgent"

    content: dict
    # The actual data being passed — flexible dict

    status: AgentStatus = AgentStatus.COMPLETE
    # Whether the sending agent succeeded

    error_message: Optional[str] = None
    # If status is FAILED — what went wrong

    sent_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyFinding(BaseModel):
    """
    A finding after Claude's Policy Reasoning Agent has analysed it.

    This is MORE detailed than a RawFinding from graph_models.py.

    DIFFERENCE:
      RawFinding (graph_models.py) = raw data from the scanner
      PolicyFinding (this file)    = after Claude has reasoned about it

    The scanner finds facts.
    Claude adds interpretation, policy mapping, and a risk score.

    REFERENCES:
      Created by: src/agents/policy_agents.py
      Consumed by: src/agents/action_agents.py (Remediation Planner)
      Saved to: src/memory/database.py (findings table)
    """
    resource_id: str
    # The Microsoft Graph item ID of the affected file
    # Same ID used to call /me/drive/items/{resource_id}/permissions

    resource_name: str
    # Human-readable file name — shown in the report

    finding_type: str
    # Category: anonymous_link, external_user_access, org_wide_link, etc.

    severity: str
    # critical, high, medium, or low

    risk_score: int
    # 1-10 numerical score — 10 is most dangerous
    # Used for sorting findings by priority

    evidence: str
    # Specific evidence Claude found — shown in the report

    policy_violated: str
    # Which governance rule this breaks
    # e.g. "Policy 3.2: No anonymous edit links on any file"

    recommended_action: str
    # What Claude recommends doing to fix it

    rollback_plan: str
    # How to undo the fix if it causes problems

    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    status: str = "open"
    # open, resolved, accepted_risk, in_progress


class RemediationAction(BaseModel):
    """
    A specific approved action to take in Microsoft 365.

    FLOW:
      PolicyFinding exists →
      Remediation Planner creates RemediationAction →
      Human Approval Agent shows it to the user →
      User approves →
      Action Executor reads this and executes it

    CRITICAL RULE:
      Only the Action Executor can execute these.
      Only after status = "approved".
      Never execute without explicit human approval.

    REFERENCES:
      Created by: src/agents/action_agents.py (RemediationPlanner)
      Approved by: src/agents/action_agents.py (HumanApprovalAgent)
      Executed by: src/agents/action_agents.py (ActionExecutor)
      Stored in: src/memory/database.py (remediations table)
    """
    finding_id: str
    # Links back to the PolicyFinding this fixes

    action_type: str
    # What to do: "remove_anonymous_link", "disable_guest_user", etc.

    resource_id: str
    # The Microsoft Graph ID of the thing to change

    resource_name: str
    # Human-readable name — shown in approval screen

    description: str
    # Plain English: "Remove anonymous edit link from Budget-2025.xlsx"

    graph_endpoint: str
    # The exact Graph API call to make when executing
    # e.g. "/me/drive/items/{id}/permissions/{permId}"

    graph_method: str = "DELETE"
    # The HTTP method: DELETE, PATCH, POST

    graph_body: Optional[dict] = None
    # The request body if method is PATCH or POST

    status: str = "proposed"
    # proposed → approved → executed → failed

    proposed_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None


class AgentState(BaseModel):
    """
    The complete state of a scan pipeline run.

    The Orchestrator creates one of these when a scan starts
    and updates it as each agent completes.

    Think of it like a job ticket at a workshop.
    It starts at the front desk and gets stamped at each station.
    At the end it has a full record of everything that happened.

    REFERENCES:
      Created by: src/agents/orchestrator.py
      Read by: every agent during the pipeline run
      Saved to: src/memory/database.py for audit purposes
    """
    scan_id: str
    # Unique ID for this scan run — used in audit logs

    request: ScanRequest
    # The original request that started this scan

    status: AgentStatus = AgentStatus.PENDING

    messages: list[AgentMessage] = Field(default_factory=list)
    # All messages passed between agents — full audit trail

    raw_findings: list[dict] = Field(default_factory=list)
    # Output of OneDriveScanner.scan_for_risks()

    policy_findings: list[PolicyFinding] = Field(default_factory=list)
    # Output of PolicyReasoningAgent

    remediation_actions: list[RemediationAction] = Field(default_factory=list)
    # Output of RemediationPlannerAgent

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    error: Optional[str] = None
    # If something went wrong — the error message
