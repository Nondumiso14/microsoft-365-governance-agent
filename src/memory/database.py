# src/memory/database.py
"""
WHAT THIS FILE IS:
  The PostgreSQL database layer.
  Defines the tables, creates them, and provides functions to read/write.

WHY POSTGRESQL AND NOT A SIMPLE FILE?
  A file disappears when the program stops.
  PostgreSQL persists data permanently.
  You can query it: "show all Critical findings from the last 30 days"
  You can see it visually in pgAdmin.
  It handles multiple users at once safely.

WHY SQLALCHEMY?
  SQLAlchemy lets you define tables as Python classes.
  It writes the SQL for you automatically.
  No SQL injection risk.
  Every senior Python developer knows it.

HOW TO SET UP POSTGRESQL LOCALLY:
  1. Open pgAdmin
  2. Right-click Databases → Create → Database
  3. Name it: m365_governance
  4. Update your .env: DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/m365_governance
  5. Run init_db() once at startup — creates all the tables

WHAT IMPORTS THIS:
  src/claude/tool_executor.py → calls save_finding()
  src/agents/action_agents.py → calls save_remediation(), get_findings()
  src/api/main.py             → calls init_db() at startup, get_db_session() per request

REFERENCES:
  agent_models.py → PolicyFinding and RemediationAction shapes match
                    the columns in Finding and Remediation tables
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    Float,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config.settings import settings

logger = logging.getLogger(__name__)


# Database engine setup

engine = create_engine(
    settings.DATABASE_URL,
    # echo=True prints every SQL query to the terminal
    # Only do this in development — too noisy for production
    echo=(settings.ENVIRONMENT == "development"),
    # pool_pre_ping tests the connection before using it
    # Prevents "connection lost" errors after idle periods
    pool_pre_ping=True,
)

# SessionLocal is a factory that creates database sessions
# Each request to FastAPI gets its own session
# Sessions are like temporary workspaces for database operations
SessionLocal = sessionmaker(
    autocommit=False,  # Never auto-commit — we control when to save
    autoflush=False,   # Never auto-flush — we control when to write
    bind=engine,
)

# Base is the parent class all our table models inherit from
Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# Table 1: findings
# Stores every risk finding the agents discover
# ─────────────────────────────────────────────────────────────

class Finding(Base):
    """
    One row = one security risk finding.

    HOW IT CONNECTS TO THE REST OF THE PROJECT:
      OneDriveScanner finds a risky permission →
      PolicyReasoningAgent scores it →
      ToolExecutor._save_finding() creates a row here →
      FastAPI /api/v1/findings reads rows from here →
      Frontend FindingsView.vue displays them

    COLUMN GUIDE:
      resource_id   = the Microsoft Graph item ID (use to call Graph again)
      resource_name = the file name (show to user)
      finding_type  = category of risk (anonymous_link, etc.)
      severity      = critical/high/medium/low
      risk_score    = 1-10 number (10 = most dangerous)
      evidence      = specific proof Claude found
      status        = open/resolved/accepted_risk/in_progress
      first_seen    = when we first found this problem
      last_seen     = updated each scan — shows if problem persists
    """
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(String(500), nullable=False, index=True)
    resource_name = Column(String(500), nullable=False)
    finding_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    risk_score = Column(Integer, default=5)
    evidence = Column(Text, nullable=False)
    policy_violated = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    rollback_plan = Column(Text, nullable=True)
    status = Column(String(50), default="open", nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(String(200), nullable=True, index=True)
    scan_id = Column(String(200), nullable=True, index=True)


# ─────────────────────────────────────────────────────────────
# Table 2: audit_log
# WRITE-ONCE — never update or delete rows here
# ─────────────────────────────────────────────────────────────


class AuditLog(Base):
    """
    Permanent record of every action taken by the system.

    NOTE:
      This table is append-only.
      NEVER run UPDATE or DELETE on audit_log.
      Once an action is recorded — it stays forever.
      This is your legal evidence trail.

    HOW IT CONNECTS:
      Every time ActionExecutor does something →
      A row is added here with a timestamp and who approved it
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(200), nullable=True, index=True)
    action_type = Column(String(100), nullable=False)
    resource_id = Column(String(500), nullable=True)
    resource_name = Column(String(500), nullable=True)
    approved_by = Column(String(200), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    outcome = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)


# ─────────────────────────────────────────────────────────────
# Table 3: remediations
# Tracks proposed and executed fixes
# ─────────────────────────────────────────────────────────────

class Remediation(Base):
    """
    One row = one proposed or executed fix.

    FLOW:
      RemediationPlannerAgent proposes a fix →
      Row created with status="proposed" →
      HumanApprovalAgent shows it to user →
      User approves → status="approved", approved_by set →
      ActionExecutor runs it → status="executed", executed_at set
    """
    __tablename__ = "remediations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(Integer, nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    resource_id = Column(String(500), nullable=False)
    resource_name = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    graph_endpoint = Column(String(500), nullable=True)
    graph_method = Column(String(10), default="DELETE")
    status = Column(String(50), default="proposed", nullable=False)
    proposed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    was_successful = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)


# ─────────────────────────────────────────────────────────────
# Database helper functions
# ─────────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Creates all tables in PostgreSQL if they do not exist.

    WHEN TO CALL THIS:
      Once at application startup — in main.py startup event.
      It is safe to call multiple times — skips existing tables.

    HOW TO VERIFY IT WORKED:
      Open pgAdmin → expand your database →
      Schemas → public → Tables →
      You should see: findings, audit_log, remediations
    """
    Base.metadata.create_all(bind=engine)
    logger.info(
        "Database tables created",
        extra={"component": "Database"}
    )


def get_db_session() -> Session:
    """
    Returns a database session for one operation.

    HOW TO USE IN FASTAPI:
      @app.get("/findings")
      def get_findings(db: Session = Depends(get_db_session)):
          return db.query(Finding).all()

    WHY SESSIONS?
      A session is like a shopping basket.
      You add things, modify things, then commit (checkout).
      If something goes wrong — you rollback (abandon the basket).
    """
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


class DatabaseManager:
    """
    Helper class with ready-made database operations.

    WHY THIS CLASS EXISTS:
      Instead of writing SQL-style queries in every agent,
      agents call simple methods like save_finding() and get_findings().
      The SQL complexity lives here — agents stay clean.

    HOW TO USE:
      db = DatabaseManager()
      finding_id = db.save_finding(resource_id="abc", ...)
      findings = db.get_open_findings()

    WHAT IMPORTS THIS:
      src/claude/tool_executor.py → db.save_finding()
      src/agents/action_agents.py → db.save_remediation(), db.get_findings()
      src/api/main.py             → db.get_open_findings(), db.get_report_data()
    """

    def __init__(self) -> None:
        self._session = SessionLocal()

    def save_finding(
        self,
        resource_id: str,
        resource_name: str,
        finding_type: str,
        severity: str,
        evidence: str,
        risk_score: int = 5,
        policy_violated: Optional[str] = None,
        recommended_action: Optional[str] = None,
        rollback_plan: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> int:
        """
        Save one finding to PostgreSQL.

        Returns the database ID of the new row.

        CALLED BY:
          src/claude/tool_executor.py → _save_finding()
        """
        finding = Finding(
            resource_id=resource_id,
            resource_name=resource_name,
            finding_type=finding_type,
            severity=severity,
            risk_score=risk_score,
            evidence=evidence,
            policy_violated=policy_violated,
            recommended_action=recommended_action,
            rollback_plan=rollback_plan,
            scan_id=scan_id,
        )
        self._session.add(finding)
        self._session.commit()
        self._session.refresh(finding)

        logger.info(
            "Finding saved",
            extra={
                "component": "DatabaseManager",
                "finding_id": finding.id,
                "severity": severity,
            }
        )
        return finding.id

    def get_open_findings(self) -> list[Finding]:
        """
        Get all findings with status = 'open'.

        CALLED BY:
          src/api/main.py → GET /api/v1/findings endpoint
          Returns the list that frontend FindingsView displays
        """
        return (
            self._session
            .query(Finding)
            .filter(Finding.status == "open")
            .order_by(Finding.risk_score.desc())
            .all()
        )

    def get_all_findings(self) -> list[Finding]:
        """Get every finding regardless of status."""
        return (
            self._session
            .query(Finding)
            .order_by(Finding.risk_score.desc())
            .all()
        )

    def mark_finding_resolved(self, finding_id: int) -> None:
        """
        Mark a finding as resolved after the fix is applied.

        CALLED BY:
          src/agents/action_agents.py → ActionExecutor
          After a remediation is successfully executed
        """
        finding = self._session.query(Finding).filter(
            Finding.id == finding_id
        ).first()
        if finding:
            finding.status = "resolved"
            self._session.commit()

    def save_remediation(
        self,
        finding_id: int,
        action_type: str,
        resource_id: str,
        resource_name: str,
        description: str,
        graph_endpoint: Optional[str] = None,
        graph_method: str = "DELETE",
    ) -> int:
        """
        Save a proposed remediation action.

        CALLED BY:
          src/agents/action_agents.py → RemediationPlannerAgent
        """
        remediation = Remediation(
            finding_id=finding_id,
            action_type=action_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            graph_endpoint=graph_endpoint,
            graph_method=graph_method,
            status="proposed",
        )
        self._session.add(remediation)
        self._session.commit()
        self._session.refresh(remediation)
        return remediation.id

    def approve_remediation(
        self,
        remediation_id: int,
        approved_by: str,
    ) -> None:
        """
        Mark a remediation as approved by a human.

        CALLED BY:
          src/api/main.py → POST /api/v1/approve endpoint
          When user clicks Approve in the frontend
        """
        remediation = self._session.query(Remediation).filter(
            Remediation.id == remediation_id
        ).first()
        if remediation:
            remediation.status = "approved"
            remediation.approved_by = approved_by
            remediation.approved_at = datetime.utcnow()
            self._session.commit()

    def get_approved_remediations(self) -> list[Remediation]:
        """
        Get all remediations approved but not yet executed.

        CALLED BY:
          src/agents/action_agents.py → ActionExecutor
          Reads this list to know what to execute
        """
        return (
            self._session
            .query(Remediation)
            .filter(Remediation.status == "approved")
            .all()
        )

    def log_audit_event(
        self,
        action_type: str,
        outcome: str,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        approved_by: Optional[str] = None,
        details: Optional[str] = None,
        scan_id: Optional[str] = None,
    ) -> None:
        """
        Write a permanent audit log entry.

        NEVER DELETE AUDIT LOG ENTRIES.
        This is your legal evidence trail.

        CALLED BY:
          src/agents/action_agents.py → ActionExecutor
          Every time an action is taken
        """
        entry = AuditLog(
            scan_id=scan_id,
            action_type=action_type,
            resource_id=resource_id,
            resource_name=resource_name,
            approved_by=approved_by,
            outcome=outcome,
            details=details,
        )
        self._session.add(entry)
        self._session.commit()
