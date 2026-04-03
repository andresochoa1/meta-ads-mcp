"""Tool implementations for Meta Ads account-level insights and pagination."""

from __future__ import annotations

from typing import Any

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.api.pagination import extract_pagination_info
from meta_ads_mcp.security import validate_id

DEFAULT_ACCOUNT_INSIGHTS_FIELDS: list[str] = [
    "account_name",
    "impressions",
    "clicks",
    "spend",
    "ctr",
    "cpc",
    "cpm",
    "reach",
    "frequency",
    "actions",
    "cost_per_action_type",
    "purchase_roas",
    "date_start",
    "date_stop",
]


def get_account_insights(
    client: MetaAPIClient,
    account_id: str,
    fields: list[str] | None = None,
    date_preset: str | None = None,
    time_range: dict[str, str] | None = None,
    time_increment: str | None = None,
    breakdowns: list[str] | None = None,
    action_breakdowns: list[str] | None = None,
    action_attribution_windows: list[str] | None = None,
    level: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Get performance insights for an entire ad account.

    This is the most comprehensive insights endpoint, supporting all
    breakdown and attribution options.

    Args:
        client: Meta API client.
        account_id: Ad account ID (e.g., 'act_123456789').
        fields: Metrics to retrieve. Defaults to standard insights fields.
        date_preset: Date range preset (today, yesterday, last_7d, last_30d, etc.).
        time_range: Custom date range {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}.
        time_increment: Time granularity (1, 7, 28, monthly, all_days).
        breakdowns: Breakdown dimensions (e.g., ['age', 'gender', 'country']).
        action_breakdowns: Action breakdown dimensions (e.g., ['action_type']).
        action_attribution_windows: Attribution windows (e.g., ['7d_click', '1d_view']).
        level: Aggregation level (ad, adset, campaign, account).
        limit: Maximum number of results (default: 25).
    """
    validate_id(account_id, "account_id")

    params: dict[str, Any] = {
        "fields": fields or DEFAULT_ACCOUNT_INSIGHTS_FIELDS,
        "limit": limit,
    }
    if date_preset is not None:
        params["date_preset"] = date_preset
    if time_range is not None:
        params["time_range"] = time_range
    if time_increment is not None:
        params["time_increment"] = time_increment
    if breakdowns is not None:
        params["breakdowns"] = breakdowns
    if action_breakdowns is not None:
        params["action_breakdowns"] = action_breakdowns
    if action_attribution_windows is not None:
        params["action_attribution_windows"] = action_attribution_windows
    if level is not None:
        params["level"] = level

    response = client.get_edge(account_id, "insights", **params)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
        "summary": response.get("summary"),
    }


def fetch_next_page(
    client: MetaAPIClient,
    url: str,
) -> dict[str, Any]:
    """Fetch the next page of results from a pagination URL.

    The URL is validated against the domain allowlist (SSRF protection)
    before making the request.

    Args:
        client: Meta API client.
        url: Pagination URL from a previous response's pagination.next_url.
    """
    response = client.fetch_url(url)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
        "summary": response.get("summary"),
    }
