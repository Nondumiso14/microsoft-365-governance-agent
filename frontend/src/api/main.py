# src/api/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.auth.token_manager import token_manager
from config.settings import settings

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode="a"),
    ]
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────
app = FastAPI(title="M365 Governance Agent", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────
# Allows Vue (localhost:5173) to call FastAPI (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────
@app.get("/")
def root() -> dict:
    return {"status": "M365 Governance Agent is running"}


# ── Auth endpoints ────────────────────────────────────────

@app.get("/auth/login")
def login() -> RedirectResponse:
    """Redirect user to Microsoft login page."""
    auth_url = token_manager.get_auth_url()
    logger.info("Redirecting user to Microsoft login")
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
def auth_callback(code: str) -> RedirectResponse:
    """
    Microsoft sends user here after login.
    Exchange code for token then redirect to Vue frontend.
    """
    token_manager.exchange_code_for_token(code)
    logger.info("User authenticated successfully")
    # Send user to Vue CallbackView which then navigates to dashboard
    return RedirectResponse(url="http://localhost:5173/callback")


@app.get("/auth/me")
def get_current_user() -> dict:
    """
    Called by Vue CallbackView to confirm login succeeded.
    """
    token = token_manager.get_cached_token()
    if not token:
        return {"authenticated": False}
    return {"authenticated": True, "access_token": "authenticated"}


@app.get("/auth/logout")
def logout() -> dict:
    """Clear token cache — forces fresh login."""
    token_manager._token_cache.clear()
    logger.info("Token cache cleared")
    return {"message": "Logged out successfully."}


# ── Scan endpoint — powers the dashboard ─────────────────

@app.get("/api/v1/scan/demo")
def demo_scan() -> dict:
    """
    Runs a real OneDrive scan.
    This is what the Dashboard calls when user clicks Run Scan.
    """
    token = token_manager.get_cached_token()

    logger.info(
        "Demo scan called",
        extra={
            "component": "ScanDemo",
            "has_token": bool(token),
        }
    )

    if not token:
        return {
            "error": "Not logged in. Visit /auth/login first.",
            "findings": [],
        }

    from src.graph.client import GraphClient
    from src.graph.onedrive import OneDriveScanner

    graph = GraphClient(access_token=token)
    scanner = OneDriveScanner(graph_client=graph)
    findings = scanner.scan_user_onedrive()

    return {
        "message": f"Scan complete. Found {len(findings)} risks.",
        "total_files_scanned": 0,
        "findings": findings,
    }


# ── Dev only — remove before production ──────────────────

@app.get("/dev/reset")
def dev_reset() -> dict:
    """Clears token cache for a clean demo."""
    token_manager._token_cache.clear()
    logger.info("Dev reset triggered")
    return {
        "message": "All caches cleared. Ready for a fresh demo.",
        "next_step": "Visit http://localhost:5173",
    }