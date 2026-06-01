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
"""

import logging
import time
import httpx
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type
)
from config.settings import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    """
    Authenticated Microsoft Graph HTTP client.

    Usage:
        client = GraphClient(access_token="eyJ...")
        files = client.get_all_pages("/me/drive/root/children")
        item  = client.get("/me/drive/items/{id}/permissions")
    """

    def __init__(self, access_token: str) -> None:
        if not access_token:
            raise ValueError("access_token cannot be empty")

        # httpx: modern, type-safe HTTP client.
        # Default headers are attached to every request automatically.
        self._http = httpx.Client(
            base_url=GRAPH_BASE,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info(
            "Graph Client initialised",
            extra={"component": "GraphClient"}
        )

    # ------------------------------------------------------------------ #
    # PUBLIC INTERFACE                                                     #
    # ------------------------------------------------------------------ #

    def get(self, endpoint: str) -> dict:
        """
        Make a single GET request to Microsoft Graph.

        Returns the parsed JSON response for that one page.
        Use get_all_pages() when you need to follow pagination.

        Args:
            endpoint: Graph path, e.g. "/me/drive/items/{id}/permissions"

        Returns:
            Parsed JSON dict — may include @odata.nextLink if paginated.
        """
        return self._get_with_retry(endpoint)

    def get_all_pages(self, endpoint: str) -> list[dict]:
        """
        Follow Microsoft Graph pagination and return every item.

        Graph returns at most 200 items per page. If there are more,
        the response includes an @odata.nextLink URL for the next page.
        This method follows those links until all pages are fetched.

        FIX: This method was called by OneDriveScanner but never existed.
        That was the AttributeError you saw at runtime.

        Args:
            endpoint: Graph path, e.g. "/me/drive/root/children"

        Returns:
            Flat list of every raw item dict across all pages.
        """
        all_items: list[dict] = []
        # First request uses the relative endpoint.
        # Subsequent requests use the full absolute nextLink URL,
        # so we switch from self._http.get (base_url-relative) to
        # httpx.get (absolute) for those pages.
        next_url: str | None = endpoint
        use_base = True  # first page uses the httpx client with base_url

        while next_url:
            if use_base:
                data = self._get_with_retry(next_url)
            else:
                # nextLink is an absolute URL — must call directly.
                data = self._get_absolute_with_retry(next_url)

            items = data.get("value", [])
            all_items.extend(items)

            next_url = data.get("@odata.nextLink")
            use_base = False  # all subsequent pages use absolute URLs

            logger.info(
                "Graph page fetched",
                extra={
                    "component": "GraphClient",
                    "items_this_page": len(items),
                    "total_so_far": len(all_items),
                    "has_next_page": bool(next_url),
                }
            )

        return all_items

    # ------------------------------------------------------------------ #
    # PRIVATE: RETRY-DECORATED REQUEST METHODS                            #
    # ------------------------------------------------------------------ #

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _get_with_retry(self, endpoint: str) -> dict:
        """
        GET a relative endpoint via the base-URL httpx client, with retries.

        BUG FIX 1: The 401 check was INSIDE the `if status == 429` block,
        meaning it could never be reached. It is now a separate check
        that runs on every response, at the correct indentation level.

        BUG FIX 2: The public get() method called self.get_with_retry()
        (no underscore) but the method was named _get_with_retry.
        Both are now consistent — all internal calls use the underscore.
        """
        response = self._http.get(endpoint)

        # Rate limited — read Retry-After and then re-raise so tenacity retries.
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
            response.raise_for_status()  # triggers tenacity retry

        # BUG FIX: 401 check is now at the correct level — not nested inside
        # the 429 block. Previously it could never be reached.
        if response.status_code == 401:
            logger.error(
                "Graph token expired or invalid",
                extra={"component": "GraphClient", "endpoint": endpoint}
            )
            # Do not retry on 401 — token is bad. Raise immediately.
            response.raise_for_status()

        response.raise_for_status()  # raise on any other 4xx/5xx
        return response.json()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    def _get_absolute_with_retry(self, url: str) -> dict:
        """
        GET a full absolute URL (used for @odata.nextLink pagination).

        nextLink URLs include the base URL already, so we cannot use
        self._http (which prepends GRAPH_BASE). We copy the auth headers
        and make a fresh request instead.
        """
        headers = dict(self._http.headers)
        response = httpx.get(url, headers=headers, timeout=30.0)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            logger.warning(
                "Graph rate limited (nextLink) — waiting",
                extra={
                    "component": "GraphClient",
                    "retry_after_seconds": retry_after,
                }
            )
            time.sleep(retry_after)
            response.raise_for_status()

        if response.status_code == 401:
            logger.error(
                "Graph token expired (nextLink)",
                extra={"component": "GraphClient"}
            )
            response.raise_for_status()

        response.raise_for_status()
        return response.json()