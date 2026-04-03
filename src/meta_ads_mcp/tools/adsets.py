"""Tool implementations for Meta Ad Set operations."""

from __future__ import annotations

from typing import Any

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.api.pagination import extract_pagination_info
from meta_ads_mcp.security import validate_id

DEFAULT_ADSET_FIELDS: list[str] = [
    "name",
    "status",
    "effective_status",
    "daily_budget",
    "lifetime_budget",
    "budget_remaining",
    "billing_event",
    "optimization_goal",
    "bid_strategy",
    "targeting",
    "created_time",
    "start_time",
    "end_time",
]

DEFAULT_ADSET_INSIGHTS_FIELDS: list[str] = [
    "adset_name",
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
    "date_start",
    "date_stop",
]


def list_adsets_by_account(
    client: MetaAPIClient,
    account_id: str,
    fields: list[str] | None = None,
    effective_status: list[str] | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List ad sets for an ad account.

    Args:
        client: Meta API client.
        account_id: Ad account ID (e.g., 'act_123456789').
        fields: Fields to retrieve. Defaults to standard ad set fields.
        effective_status: Filter by status (e.g., ['ACTIVE', 'PAUSED']).
        limit: Maximum number of ad sets to return (default: 25).
    """
    validate_id(account_id, "account_id")

    params: dict[str, Any] = {
        "fields": fields or DEFAULT_ADSET_FIELDS,
        "limit": limit,
    }
    if effective_status is not None:
        params["effective_status"] = effective_status

    response = client.get_edge(account_id, "adsets", **params)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
    }


def list_adsets_by_campaign(
    client: MetaAPIClient,
    campaign_id: str,
    fields: list[str] | None = None,
    effective_status: list[str] | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List ad sets for a specific campaign.

    Args:
        client: Meta API client.
        campaign_id: Campaign ID.
        fields: Fields to retrieve. Defaults to standard ad set fields.
        effective_status: Filter by status (e.g., ['ACTIVE', 'PAUSED']).
        limit: Maximum number of ad sets to return (default: 25).
    """
    validate_id(campaign_id, "campaign_id")

    params: dict[str, Any] = {
        "fields": fields or DEFAULT_ADSET_FIELDS,
        "limit": limit,
    }
    if effective_status is not None:
        params["effective_status"] = effective_status

    response = client.get_edge(campaign_id, "adsets", **params)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
    }


def get_adset(
    client: MetaAPIClient,
    adset_id: str,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Get details of a specific ad set.

    Args:
        client: Meta API client.
        adset_id: Ad set ID.
        fields: Fields to retrieve. Defaults to standard ad set fields.
    """
    validate_id(adset_id, "adset_id")

    response = client.get_node(
        adset_id,
        fields=fields or DEFAULT_ADSET_FIELDS,
    )

    return {"data": response}


def get_adset_insights(
    client: MetaAPIClient,
    adset_id: str,
    fields: list[str] | None = None,
    date_preset: str | None = None,
    time_range: dict[str, str] | None = None,
    time_increment: str | None = None,
    breakdowns: list[str] | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Get performance insights for a specific ad set.

    Args:
        client: Meta API client.
        adset_id: Ad set ID.
        fields: Metrics to retrieve. Defaults to standard insights fields.
        date_preset: Date range preset (today, yesterday, last_7d, last_30d, etc.).
        time_range: Custom date range {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}.
        time_increment: Time granularity (1, 7, 28, monthly, all_days).
        breakdowns: Breakdown dimensions (e.g., ['age', 'gender']).
        limit: Maximum number of results (default: 25).
    """
    validate_id(adset_id, "adset_id")

    params: dict[str, Any] = {
        "fields": fields or DEFAULT_ADSET_INSIGHTS_FIELDS,
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

    response = client.get_edge(adset_id, "insights", **params)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
        "summary": response.get("summary"),
    }
