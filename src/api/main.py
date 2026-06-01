# src/api/main.py
import logging
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Import the shared INSTANCE — not the class
# token_manager.py already creates one shared instance at the bottom
# Importing the class and calling TokenManager() creates a SECOND
# separate instance — they have separate caches and never talk to each other
from src.auth.token_manager import token_manager
from config.settings import settings

# Configure logging to write to both console AND a log file
# 
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        # Handler 1: print logs to the terminal
        logging.StreamHandler(),
        # Handler 2: write logs to a file you can open and read
        # File lives at the root of your project: app.log
        logging.FileHandler("app.log", mode="a"),
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="M365 Governance Agent", version="1.0.0")


@app.get("/")
def root() -> dict:
    return {"status": "M365 Governance Agent is running"}


@app.get("/auth/login")
def login() -> RedirectResponse:
    """Send the user to the Microsoft login page."""
    auth_url = token_manager.get_auth_url()
    logger.info("Redirecting user to Microsoft login")
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
def auth_callback(code: str) -> dict:
    """Microsoft sends the user back here after login with a code."""
    token = token_manager.exchange_code_for_token(code)
    logger.info("User authenticated successfully")
    return {
        "message": "Authentication successful",
        "token_type": token.get("token_type")
    }


@app.get("/auth/logout")
def logout() -> dict:
    """
    Clears the token cache.
    Forces a fresh login next time without restarting the server.
    """
    token_manager._token_cache.clear()
    logger.info("Token cache cleared — user logged out")
    return {
        "message": "Logged out successfully.",
        "next_step": "Visit /auth/login to log in again."
    }


@app.get("/api/v1/scan/demo")
def demo_scan() -> dict:
    """
    Demo endpoint — runs a real OneDrive scan.
    Visit this in the browser to see real findings.
    """
    token = token_manager.get_cached_token()

    # Add this logging line so you can see the cache state
    logger.info(
        "Demo scan called",
        extra={
            "component": "ScanDemo",
            "cache_keys": list(token_manager._token_cache.keys()),
            "has_token": bool(token),
        }
    )

    if not token:
        return {
            "error": "Not logged in. Visit /auth/login first.",
            "hint": "Make sure you complete the full login at /auth/login before calling this endpoint"
        }

    from src.graph.client import GraphClient
    from src.graph.onedrive import OneDriveScanner

    graph = GraphClient(access_token=token)
    scanner = OneDriveScanner(graph_client=graph)
    findings = scanner.scan_user_onedrive()

    return {
        "message": f"Scan complete. Found {len(findings)} risks.",
        "findings": findings
    }

@app.get("/dev/reset")
def dev_reset() -> dict:
    """
    Development only — clears everything for a clean demo.
    REMOVE THIS before going to production.
    """
    if settings.ENVIRONMENT != "development":
        return {"error": "Not available in production"}

    token_manager._token_cache.clear()
    logger.info("Dev reset triggered — all caches cleared")
    return {
        "message": "All caches cleared. Ready for a fresh demo.",
        "next_step": "Visit http://localhost:8000/auth/login"
    }