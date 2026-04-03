"""Meta Graph API client with security and rate limiting."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import structlog

from meta_ads_mcp import __version__
from meta_ads_mcp.api.rate_limiter import RateLimiter
from meta_ads_mcp.config import ServerConfig
from meta_ads_mcp.security import redact_sensitive_params, validate_id, validate_url

logger = structlog.get_logger()

# HTTP status codes that are safe to retry (transient errors)
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class MetaAPIClient:
    """Secure client for Meta Graph API.

    Security model:
    - Token is NEVER logged or included in error messages
    - All URLs are validated against domain allowlist
    - All IDs are validated against expected patterns
    - Rate limiting is enforced per-account
    """

    def __init__(
        self,
        config: ServerConfig,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._config = config
        self._token = config.meta.access_token
        self._base_url = config.meta.graph_url
        self._rate_limiter = rate_limiter
        self._client = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,  # Never follow redirects (SSRF protection)
            headers={"User-Agent": f"meta-ads-mcp/{__version__}"},
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    def _build_params(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build request parameters with access token."""
        result: dict[str, Any] = {"access_token": self._token}
        if params:
            result.update(params)
        return result

    def get_node(self, node_id: str, **kwargs: Any) -> dict[str, Any]:
        """Fetch a single node by ID.

        Args:
            node_id: Meta object ID (validated against pattern).
            **kwargs: Additional query parameters (fields, etc.)
        """
        validate_id(node_id, "node_id")
        url = f"{self._base_url}/{node_id}"
        return self._request(url, kwargs)

    def get_edge(self, parent_id: str, edge_name: str, **kwargs: Any) -> dict[str, Any]:
        """Fetch an edge (collection) from a parent node.

        Args:
            parent_id: Parent object ID (validated).
            edge_name: Edge name (e.g., 'campaigns', 'insights').
            **kwargs: Additional query parameters.
        """
        validate_id(parent_id, "parent_id")
        url = f"{self._base_url}/{parent_id}/{edge_name}"
        return self._request(url, kwargs)

    def get_me(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch the current user's data."""
        url = f"{self._base_url}/me"
        return self._request(url, kwargs)

    def fetch_url(self, url: str) -> dict[str, Any]:
        """Fetch a pre-built URL (e.g., pagination URL).

        The URL is validated against the domain allowlist before fetching.
        This prevents SSRF attacks through pagination URLs.
        """
        validate_url(url)
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def _request(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GET request with security controls and retry logic.

        - Token is added to params (not logged)
        - Errors never expose token
        - All requests logged with redacted params
        - Rate limiter (if present) throttles requests
        - Transient HTTP errors (429, 5xx) are retried with exponential backoff
        """
        full_params = self._build_params(self._prepare_params(params or {}))
        safe_params = redact_sensitive_params(full_params)

        logger.debug("api_request", url=url, params=safe_params)

        attempt = 0
        while True:
            # Acquire rate limit token before each attempt
            if self._rate_limiter is not None:
                self._rate_limiter.acquire_or_wait()

            try:
                response = self._client.get(url, params=full_params)
                response.raise_for_status()
                data = response.json()
                logger.debug("api_response", url=url, status=response.status_code)
                return data
            except httpx.HTTPStatusError as e:
                status = e.response.status_code

                # Check if we should retry this status code
                if self._rate_limiter is not None and status in _RETRYABLE_STATUS_CODES:
                    should_retry, delay = self._rate_limiter.should_retry(status, attempt)
                    if should_retry:
                        attempt += 1
                        time.sleep(delay)
                        continue

                # Not retryable or retries exhausted — raise
                logger.error(
                    "api_error",
                    url=url,
                    status=status,
                    params=safe_params,  # SAFE — token redacted
                )
                raise
            except httpx.RequestError as e:
                logger.error("api_connection_error", url=url, error=str(e))
                raise

    def _prepare_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Prepare parameters for the Meta Graph API.

        Handles type conversions:
        - Lists of strings -> comma-joined
        - Dicts and lists -> JSON encoded
        - Booleans -> 'true'/'false' strings
        """
        prepared: dict[str, Any] = {}

        # Fields that should be comma-joined
        join_fields = {
            "fields",
            "action_attribution_windows",
            "action_breakdowns",
            "breakdowns",
        }

        # Fields that should be JSON-encoded
        json_fields = {
            "filtering",
            "time_range",
            "time_ranges",
            "effective_status",
            "special_ad_categories",
            "objective",
        }

        for key, value in params.items():
            if value is None:
                continue
            elif key in join_fields and isinstance(value, list):
                prepared[key] = ",".join(str(v) for v in value)
            elif key in json_fields and isinstance(value, (list, dict)):
                prepared[key] = json.dumps(value)
            elif isinstance(value, bool):
                prepared[key] = "true" if value else "false"
            else:
                prepared[key] = value

        return prepared

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> MetaAPIClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
