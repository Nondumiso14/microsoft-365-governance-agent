import logging
import msal
from config.settings import settings

logger = logging.getLogger(__name__)

# Updated scopes — no admin permissions
SCOPES = [
    #NOTE: that openid, profile, offline_access raise value errors when they're added in with the scopes because msal generates then 
    #dynamically at login.
    #"openid",
    #"profile",
    #"offline_access",

    "email", # so we know who is logged in
    "User.Read", # to read the logged in user's basic profile
    "Files.Read", # to read their OneDrive files
    "Files.ReadWrite",  # o read and write their OneDrive files
]


class TokenManager:
    def __init__(self) -> None:
        self._client = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=(
                f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
            ),
            token_cache = msal.TokenCache()
        )
        self._token_cache: dict[str, str] = {}

        # In-memory token cache — one token per user session
        # In production this moves to Redis or a database
        self._token_cache: dict[str, str] = {}
        logger.info(
            "TokenManager initialised",
            extra={"component": "TokenManager"}
        )

    def get_auth_url(self) -> str:
        """
        Build the Microsoft login URL.
        Send the user here to begin the login flow.
        """
        url = self._client.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
            prompt = "consent",
            login_hint= None,
            
        )
        logger.info(
            "Auth URL generated",
            extra={"component": "TokenManager"}
        )
        return url

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Step 2 of login — swap the authorization code for tokens.

        Microsoft sends a one-time code to our callback URL.
        We exchange it here for:
          - access_token: use this to call Graph API right now
          - refresh_token: use this to get new access tokens later
          - id_token: contains user identity information

        NEVER log or store the raw token values in plain text.
        """
        result = self._client.acquire_token_by_authorization_code(
            code=code,
            scopes=SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
        )

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

        # Cache the token keyed by the user's object ID
        user_id = result.get("id_token_claims", {}).get("oid", "default")
        self._token_cache[user_id] = result["access_token"]

        logger.info(
            "Token acquired and cached",
            extra={"component": "TokenManager", "user_id": user_id}
        )
        return result

    def get_cached_token(self, user_id: str = "default") -> str | None:
        """
        Retrieve a cached access token for a user.

        Returns None if no token is cached — caller must redirect to login.
        """
        return self._token_cache.get(user_id)


# Single shared instance
token_manager = TokenManager()