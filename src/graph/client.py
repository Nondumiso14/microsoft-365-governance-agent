# src/graph/client.py
"""
Microsoft Graph HTTP client.

WHAT THIS DOES:
  Makes authenticated HTTP requests to the Microsoft Graph API.
  Every request includes the user's access token as a Bearer header.

WHY TENACITY FOR RETRIES:
  Microsoft Graph returns HTTP 429 (Too Many Requests) when you call
  it too fast. The response includes a Retry-After header telling you
  exactly how many seconds to wait. Our retry logic reads that header.

  Without this: your scanner crashes halfway through a large scan.
  With this: it waits politely and continues. Professional behaviour.

WHAT YOU SHOULD HAVE TRIED YOURSELF FIRST:
  - How do you attach a Bearer token to an HTTP request?
  - What header name does Graph expect?
  - What does a 429 response look like?
  - How do you read the Retry-After header value?
"""

import logging
import time
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config.settings import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    """
    Authenticated Microsoft Graph HTTP client.

    Usage:
        client = GraphClient(access_token="eyJ...")
        sites = client.get("/me/drive/root/children")
    """

    def __init__(self, access_token: str) -> None:
        if not access_token:
            raise ValueError("access_token cannot be empty")

        # httpx is a modern, type-safe HTTP client
        # We set default headers here — every request gets them automatically
        self._http = httpx.Client(
            base_url=GRAPH_BASE,
            headers={
                # This is how Graph authenticates every request
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info(
            "GraphClient initialised",
            extra={"component": "GraphClient"}
        )

    def get(self, endpoint: str) -> dict:
        """
        Make a GET request to Microsoft Graph.

        Handles:
          - 429 rate limiting with Retry-After respect
          - 401 token expiry detection
          - Automatic pagination signal (returns @odata.nextLink if present)

        Args:
            endpoint: The Graph path e.g. "/me/drive/root/children"

        Returns:
            Parsed JSON response as a dict
        """
        return self._get_with_retry(endpoint)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _get_with_retry(self, endpoint: str) -> dict:
        response = self._http.get(endpoint)

        # Handle rate limiting — read the Retry-After header
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            logger.warning(
                "Graph rate limited — waiting",
                extra={
                    "component": "GraphClient",
                    "retry_after_seconds": retry_after,
                    "endpoint": endpoint,
                }
            )
            time.sleep(retry_after)
            response.raise_for_status()  # Triggers tenacity retry

        # 401 means token expired — do not retry, signal the caller
        if response.status_code == 401:
            logger.error(
                "Graph token expired or invalid",
                extra={"component": "GraphClient", "endpoint": endpoint}
            )
            raise PermissionError("Access token expired. User must re-authenticate.")

        response.raise_for_status()
        return response.json()

    def get_all_pages(self, endpoint: str) -> list[dict]:
        """
        Fetch ALL pages of a paginated Graph response.

        WHY THIS EXISTS:
          Graph returns a maximum of 200 items per request.
          If a folder has 500 files, you get the first 200 and a
          @odata.nextLink URL pointing to the next page.
          This method follows those links until everything is fetched.

        Senior rule: Never assume one page is all the data.
        Always handle pagination on any list endpoint.
        """
        all_items: list[dict] = []
        next_url: str | None = endpoint

        while next_url:
            data = self.get(next_url)
            items = data.get("value", [])
            all_items.extend(items)

            # Graph puts the next page URL here
            next_url = data.get("@odata.nextLink")

            logger.info(
                "Graph page fetched",
                extra={
                    "component": "GraphClient",
                    "items_fetched": len(items),
                    "total_so_far": len(all_items),
                    "has_more": bool(next_url),
                }
            )

        return all_items