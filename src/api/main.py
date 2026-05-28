import logging
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.auth.token_manager import TokenManager
from config.settings import settings

logging.basicConfig(level="INFO",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),   # This creates the physical file
        logging.StreamHandler()          # This keeps printing logs to the terminal too
    ])
logger = logging.getLogger(__name__)

app = FastAPI(title="M365 Governance Agent", version="1.0.0")
token_manager = TokenManager()

@app.get("/")
def root() -> dict:
    return {"status": "M365 Governance Agent is running"}

@app.get("/auth/login")
def login() -> RedirectResponse:
    """Send the user to Microsoft login page."""
    auth_url = token_manager.get_auth_url()
    logger.info("Redirecting user to Microsoft login")
    return RedirectResponse(url=auth_url)

@app.get("/auth/callback")
def auth_callback(code: str) -> dict:
    """Microsoft sends the user back here after login with a code."""
    token = token_manager.exchange_code_for_token(code)
    logger.info("User authenticated successfully")
    return {"message": "Authentication successful", "token_type": token.get("token_type")}

@app.get("/auth/logout")
def logout() -> dict:

    token_manager._token_cache.clear()

    logger.info("Token cache cleared- user logged out")
    return{"messahe" : "Logged out successfully. Visit /auth/login to start again."}

@app.get("dev/reset")
def dev_reset() -> dict:

    if settings.ENVIRONMENT != "development":
        return{"error" : "Not available in production"}
    
    #Clear token cache
    token_manager._token_cache.clear()

    logger.info("Dev reset cleard.")

    return {
        "messages": "All caches cleared. Ready for fresh demo",
        "nest_step" : "Visit http://localhost:8000/auth/login"}