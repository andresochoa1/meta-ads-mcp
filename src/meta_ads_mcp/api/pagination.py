"""Safe pagination with domain validation for Meta Graph API."""

from __future__ import annotations

from typing import Any

import structlog

from meta_ads_mcp.security import validate_url

logger = structlog.get_logger()


def extract_pagination_info(response: dict[str, Any]) -> dict[str, Any]:
    """Extract pagination metadata from a Meta API response.

    Returns a dict with:
        - has_next: bool
        - has_previous: bool
        - next_url: str | None (validated against domain allowlist)
        - previous_url: str | None (validated against domain allowlist)
        - after_cursor: str | None
        - before_cursor: str | None
    """
    paging = response.get("paging", {})
    cursors = paging.get("cursors", {})

    next_url = paging.get("next")
    previous_url = paging.get("previous")

    # Validate pagination URLs against allowlist
    if next_url:
        try:
            validate_url(next_url)
        except ValueError:
            logger.warning("pagination_url_blocked", url_type="next", url=next_url)
            next_url = None

    if previous_url:
        try:
            validate_url(previous_url)
        except ValueError:
            logger.warning("pagination_url_blocked", url_type="previous", url=previous_url)
            previous_url = None

    return {
        "has_next": next_url is not None,
        "has_previous": previous_url is not None,
        "next_url": next_url,
        "previous_url": previous_url,
        "after_cursor": cursors.get("after"),
        "before_cursor": cursors.get("before"),
    }
