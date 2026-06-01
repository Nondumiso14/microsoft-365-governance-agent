# src/models/risk_models.py
"""
WHAT THIS FILE IS:
  Models for the final governance report — what the user sees
  at the end of a scan.

WHY THIS EXISTS:
  The raw findings and policy findings are internal data.
  The GovernanceReport is what gets shown to the user —
  a clean, professional summary of everything found.

WHAT IMPORTS THIS:
  src/agents/action_agents.py  → creates GovernanceReport
  src/api/main.py              → returns GovernanceReport to the frontend
  frontend DashboardView.vue   → displays this data

BEGINNER TIP — THE FLOW OF DATA:
  1. OneDriveScanner  → list[dict]         (raw, no structure)
  2. PolicyFinding    → list[PolicyFinding] (structured, Claude-analysed)
  3. GovernanceReport → one clean object    (ready to show the user)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    """
    A count of findings by severity level.

    Shown at the top of the dashboard as the four stat boxes:
    Critical: 2  |  High: 5  |  Medium: 8  |  Low: 3

    REFERENCES:
      Used inside: GovernanceReport
      Displayed by: frontend DashboardView.vue stat boxes
    """
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0

    @property
    def has_critical_risks(self) -> bool:
        """True if any critical findings exist — used to set alert level."""
        return self.critical > 0


class FindingSummary(BaseModel):
    """
    A single finding formatted for the frontend to display.

    Simpler than PolicyFinding — only the fields the UI needs.

    REFERENCES:
      Created from: PolicyFinding (in action_agents.py)
      Used inside: GovernanceReport.findings
      Displayed by: frontend FindingsView.vue table rows
    """
    id: str
    resource_name: str
    finding_type: str
    severity: str
    risk_score: int
    evidence: str
    recommended_action: str
    status: str = "open"


class GovernanceReport(BaseModel):
    """
    The final output of a complete governance scan.

    This is what the frontend displays to the user.
    It is also what gets stored in PostgreSQL for historical comparison.

    FLOW:
      All 10 agents complete →
      ActionAgent.create_report() builds this →
      FastAPI /api/v1/report endpoint returns it →
      Vue DashboardView displays it

    EXAMPLE:
      GovernanceReport(
          scan_id="scan-001",
          tenant_name="Kion Consulting",
          files_scanned=247,
          summary=RiskSummary(critical=1, high=3, medium=5, low=2, total=11),
          findings=[...],
          generated_at=datetime.utcnow()
      )
    """
    scan_id: str
    tenant_name: str = "Your Organisation"
    files_scanned: int = 0
    permissions_checked: int = 0

    summary: RiskSummary
    # The four stat boxes at the top of the dashboard

  # All findings sorted by risk_score descending (highest first)
    findings: list[FindingSummary] = Field(default_factory=list)
    

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    scan_duration_seconds: Optional[float] = None

     # Claude-generated plain English summary of what was found
    # e.g. "1 critical finding requires immediate attention.
    #       A budget file has an anonymous edit link."

    executive_summary: Optional[str] = None
   