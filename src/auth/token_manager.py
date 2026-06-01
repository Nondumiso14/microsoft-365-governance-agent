# src/auth/token_manager.py
import logging
import msal
from config.settings import settings

logger = logging.getLogger(__name__)

SCOPES = [
    # openid, profile, offline_access removed from here
    # MSAL adds them automatically — adding them manually
    # causes duplicate scope errors from Microsoft
    "email", # so we know who is logged in
    "User.Read", # to read the logged in user's basic profile
    "Files.Read", # to read their OneDrive files
    "Files.ReadWrite", # o read and write their OneDrive files
]


class TokenManager:
    def __init__(self) -> None:
        # Stored as self._client
        # Every method must use self._client — not self.client
        # The underscore means "private to this class"
        self._client = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=(
                f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
            ),
            # Fresh empty cache every server restart
            # This forces a new login every time the server starts
            token_cache=msal.TokenCache()
        )

        # Fresh dictionary — cleared on every server restart
        self._token_cache: dict[str, str] = {}

        logger.info(
            "TokenManager initialised — cache cleared",
            extra={"component": "TokenManager"}
        )

    def get_auth_url(self) -> str:
        """
        Step 1 — Build the Microsoft login URL.
        Send the user to this URL to begin the login flow.
        """
        url = self._client.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
            prompt="consent",  
            login_hint=None ,
        )
        logger.info(
            "Auth URL generated",
            extra={"component": "TokenManager"}
        )
        return url

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Step 2 — Swap the one-time code for an access token.

        Microsoft sends a code to our callback URL after login.
        We exchange it here for the real access token.
        """
        result = self._client.acquire_token_by_authorization_code(
            code=code,
            scopes=SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
        )

        # Raise an exception immediately on failure
        # Do not silently continue — fail loudly so the caller knows
        if "error" in result:
            logger.error(
                "Token exchange failed",
                extra={
                    "component": "TokenManager",
                    "error": result.get("error"),
                    "description": result.get("error_description"),
                }
            )
            raise ValueError(
                f"Token acquisition failed: {result.get('error_description')}"
            )

        # Token caching is OUTSIDE the error block
        # It runs only when login SUCCEEDS — which is correct
        user_id = result.get("id_token_claims", {}).get("oid", "default")
        self._token_cache[user_id] = result["access_token"]

        # "default" key — for simple lookups like the demo endpoint
        # This means get_cached_token() with no arguments always works
        self._token_cache["default"] = result["access_token"]

        logger.info(
            "Token acquired and cached",
            extra={"component": "TokenManager", "user_id": user_id}
        )

        return result

    def get_cached_token(self, user_id: str = "default") -> str | None:
        """
        Retrieve a cached access token for a user.
        Returns None if no token cached — caller must redirect to login.
        """
        return self._token_cache.get(user_id)


# Single shared instance — import THIS in other files
# Never create a new TokenManager() anywhere else
token_manager = TokenManager()