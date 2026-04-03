"""MCP Resources for Meta Ads campaign data.

Resources provide read-only data snapshots that can be used as context
by LLMs without requiring explicit tool calls.
"""

from __future__ import annotations

import json

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.security import validate_id


def get_accounts_resource(client: MetaAPIClient) -> str:
    """Resource: meta://accounts -- list of accessible ad accounts.

    Returns a JSON string with all ad accounts the token has access to,
    including name, ID, status, and currency.
    """
    result = client.get_me(
        fields="adaccounts{name,account_id,account_status,currency}"
    )
    accounts = result.get("adaccounts", {}).get("data", [])
    return json.dumps({"accounts": accounts}, indent=2)


def get_account_campaigns_resource(
    client: MetaAPIClient, account_id: str
) -> str:
    """Resource: meta://accounts/{id}/campaigns -- active campaigns for an account.

    Returns a JSON string with all active campaigns including name, status,
    objective, and budget information.
    """
    validate_id(account_id, "account_id")

    result = client.get_edge(
        account_id,
        "campaigns",
        fields=[
            "name",
            "status",
            "objective",
            "daily_budget",
            "lifetime_budget",
        ],
        effective_status=["ACTIVE"],
        limit=100,
    )
    return json.dumps({"campaigns": result.get("data", [])}, indent=2)


def get_account_summary_resource(
    client: MetaAPIClient, account_id: str
) -> str:
    """Resource: meta://accounts/{id}/summary -- executive summary for an account.

    Returns a JSON string combining account details with last 7 days of
    performance data for a quick executive overview.
    """
    validate_id(account_id, "account_id")

    details = client.get_node(
        account_id,
        fields=[
            "name",
            "account_status",
            "balance",
            "amount_spent",
            "currency",
        ],
    )

    insights = client.get_edge(
        account_id,
        "insights",
        fields=[
            "spend",
            "impressions",
            "clicks",
            "ctr",
            "cpc",
            "cpm",
            "actions",
        ],
        date_preset="last_7d",
    )

    return json.dumps(
        {
            "account": details,
            "last_7d_performance": insights.get("data", []),
        },
        indent=2,
    )
