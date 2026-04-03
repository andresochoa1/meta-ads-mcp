"""Tool implementations for Meta Ad Account operations."""

from __future__ import annotations

from typing import Any

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.api.pagination import extract_pagination_info
from meta_ads_mcp.security import validate_id

DEFAULT_ACCOUNT_FIELDS: list[str] = [
    "name",
    "business_name",
    "account_status",
    "balance",
    "amount_spent",
    "currency",
    "created_time",
    "account_id",
]


def list_ad_accounts(client: MetaAPIClient) -> dict[str, Any]:
    """List all ad accounts accessible with the current access token.

    Returns accounts with name, ID, status, currency, balance, and spend.
    """
    response = client.get_me(
        fields="adaccounts{name,account_id,account_status,currency,balance,amount_spent}"
    )

    adaccounts = response.get("adaccounts", {})

    return {
        "data": adaccounts.get("data", []),
        "pagination": extract_pagination_info(adaccounts),
    }


def get_ad_account_details(
    client: MetaAPIClient,
    account_id: str,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Get detailed information about a specific ad account.

    Args:
        client: Meta API client.
        account_id: Ad account ID (e.g., 'act_123456789').
        fields: Fields to retrieve. Defaults to standard account fields.
    """
    validate_id(account_id, "account_id")

    response = client.get_node(
        account_id,
        fields=fields or DEFAULT_ACCOUNT_FIELDS,
    )

    return {"data": response}


def get_ad_account_activities(
    client: MetaAPIClient,
    account_id: str,
    limit: int = 25,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """Get activity log for an ad account.

    Args:
        client: Meta API client.
        account_id: Ad account ID (e.g., 'act_123456789').
        limit: Maximum number of activities to return (default: 25).
        since: Start date filter (ISO 8601 or Unix timestamp).
        until: End date filter (ISO 8601 or Unix timestamp).
    """
    validate_id(account_id, "account_id")

    params: dict[str, Any] = {"limit": limit}
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until

    response = client.get_edge(account_id, "activities", **params)

    return {
        "data": response.get("data", []),
        "pagination": extract_pagination_info(response),
    }
