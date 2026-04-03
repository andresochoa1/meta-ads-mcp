"""Meta Ads MCP Server — main entry point.

Registers all tools, resources, and prompts for the MCP protocol.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)

from meta_ads_mcp.api.client import MetaAPIClient
from meta_ads_mcp.config import load_config
from meta_ads_mcp.prompts.analysis import PROMPTS, get_prompt_messages
from meta_ads_mcp.resources import campaign_data
from meta_ads_mcp.security import configure_logging
from meta_ads_mcp.tools import accounts, ads, adsets, campaigns, creatives, insights

logger = structlog.get_logger()

# Server instance
app = Server("meta-ads-mcp")

# Global client — initialized on startup
_client: MetaAPIClient | None = None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Register all 18 Meta Ads tools."""
    return [
        # --- Accounts (3) ---
        Tool(
            name="list_ad_accounts",
            description=(
                "List all ad accounts accessible with the current access token. "
                "Returns account name, ID, status, currency, balance, and spend."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_ad_account_details",
            description=(
                "Get detailed information about a specific ad account including "
                "business name, status, balance, spend, and creation date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to retrieve (optional, uses defaults)",
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_ad_account_activities",
            description=(
                "Get the activity log for an ad account. Shows changes made to "
                "campaigns, ad sets, and ads."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of activities (default: 25)",
                        "default": 25,
                    },
                    "since": {
                        "type": "string",
                        "description": "Start date filter (ISO 8601 or Unix timestamp)",
                    },
                    "until": {
                        "type": "string",
                        "description": "End date filter (ISO 8601 or Unix timestamp)",
                    },
                },
                "required": ["account_id"],
            },
        ),
        # --- Campaigns (3) ---
        Tool(
            name="list_campaigns",
            description=(
                "List campaigns for an ad account. Can filter by status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve (optional, uses defaults)",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status (e.g., ['ACTIVE', 'PAUSED'])",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of campaigns (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="get_campaign",
            description=(
                "Get details of a specific campaign including name, status, "
                "objective, budget, and schedule."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve (optional, uses defaults)",
                    },
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="get_campaign_insights",
            description=(
                "Get performance metrics for a specific campaign. Supports "
                "date presets, custom ranges, breakdowns, and time increments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to retrieve (e.g., impressions, clicks, spend)",
                    },
                    "date_preset": {
                        "type": "string",
                        "description": (
                            "Date range preset (today, yesterday, last_7d, last_30d, "
                            "this_month, last_month, etc.)"
                        ),
                    },
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "since": {"type": "string", "description": "Start date YYYY-MM-DD"},
                            "until": {"type": "string", "description": "End date YYYY-MM-DD"},
                        },
                        "description": "Custom date range",
                    },
                    "time_increment": {
                        "type": "string",
                        "description": "Time granularity (1, 7, 28, monthly, all_days)",
                    },
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Breakdown dimensions (e.g., age, gender, country)",
                    },
                    "level": {
                        "type": "string",
                        "description": "Aggregation level (ad, adset, campaign, account)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["campaign_id"],
            },
        ),
        # --- Ad Sets (4) ---
        Tool(
            name="list_adsets_by_account",
            description="List ad sets for an ad account. Can filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="list_adsets_by_campaign",
            description="List ad sets for a specific campaign. Can filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="get_adset",
            description=(
                "Get details of a specific ad set including targeting, "
                "budget, optimization goal, and schedule."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {
                        "type": "string",
                        "description": "Ad set ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                },
                "required": ["adset_id"],
            },
        ),
        Tool(
            name="get_adset_insights",
            description=(
                "Get performance metrics for a specific ad set. Supports "
                "date presets, custom ranges, and breakdowns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {
                        "type": "string",
                        "description": "Ad set ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to retrieve",
                    },
                    "date_preset": {
                        "type": "string",
                        "description": "Date range preset",
                    },
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "since": {"type": "string"},
                            "until": {"type": "string"},
                        },
                        "description": "Custom date range",
                    },
                    "time_increment": {
                        "type": "string",
                        "description": "Time granularity",
                    },
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Breakdown dimensions",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["adset_id"],
            },
        ),
        # --- Ads (4) ---
        Tool(
            name="list_ads_by_account",
            description="List ads for an ad account. Can filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="list_ads_by_campaign",
            description="List ads for a specific campaign. Can filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {
                        "type": "string",
                        "description": "Campaign ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["campaign_id"],
            },
        ),
        Tool(
            name="list_ads_by_adset",
            description="List ads for a specific ad set. Can filter by status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {
                        "type": "string",
                        "description": "Ad set ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "effective_status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["adset_id"],
            },
        ),
        Tool(
            name="get_ad_insights",
            description=(
                "Get performance metrics for a specific ad. Supports "
                "date presets, custom ranges, and breakdowns."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {
                        "type": "string",
                        "description": "Ad ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to retrieve",
                    },
                    "date_preset": {
                        "type": "string",
                        "description": "Date range preset",
                    },
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "since": {"type": "string"},
                            "until": {"type": "string"},
                        },
                        "description": "Custom date range",
                    },
                    "time_increment": {
                        "type": "string",
                        "description": "Time granularity",
                    },
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Breakdown dimensions",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["ad_id"],
            },
        ),
        # --- Creatives (2) ---
        Tool(
            name="get_creative",
            description=(
                "Get details of a specific ad creative including title, body, "
                "image URL, and object story spec."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "creative_id": {
                        "type": "string",
                        "description": "Ad creative ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                },
                "required": ["creative_id"],
            },
        ),
        Tool(
            name="list_creatives_by_ad",
            description="List ad creatives associated with a specific ad.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_id": {
                        "type": "string",
                        "description": "Ad ID",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to retrieve",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["ad_id"],
            },
        ),
        # --- Insights (2) ---
        Tool(
            name="get_account_insights",
            description=(
                "Get comprehensive performance insights for an entire ad account. "
                "Supports all breakdown, attribution, and aggregation options."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Ad account ID (e.g., 'act_123456789')",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to retrieve",
                    },
                    "date_preset": {
                        "type": "string",
                        "description": "Date range preset",
                    },
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "since": {"type": "string"},
                            "until": {"type": "string"},
                        },
                        "description": "Custom date range",
                    },
                    "time_increment": {
                        "type": "string",
                        "description": "Time granularity",
                    },
                    "breakdowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Breakdown dimensions",
                    },
                    "action_breakdowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Action breakdown dimensions (e.g., action_type)",
                    },
                    "action_attribution_windows": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Attribution windows (e.g., 7d_click, 1d_view)",
                    },
                    "level": {
                        "type": "string",
                        "description": "Aggregation level (ad, adset, campaign, account)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 25)",
                        "default": 25,
                    },
                },
                "required": ["account_id"],
            },
        ),
        Tool(
            name="fetch_next_page",
            description=(
                "Fetch the next page of results using a pagination URL. "
                "The URL is validated against the domain allowlist for SSRF protection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "Pagination URL from a previous response's pagination.next_url"
                        ),
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to their implementations."""
    if _client is None:
        return [
            TextContent(
                type="text",
                text="Error: server not initialized. No API client available.",
            )
        ]

    # Tool dispatch table
    tool_handlers: dict[str, Any] = {
        # Accounts
        "list_ad_accounts": lambda: accounts.list_ad_accounts(_client),
        "get_ad_account_details": lambda: accounts.get_ad_account_details(
            _client,
            account_id=arguments["account_id"],
            fields=arguments.get("fields"),
        ),
        "get_ad_account_activities": lambda: accounts.get_ad_account_activities(
            _client,
            account_id=arguments["account_id"],
            limit=arguments.get("limit", 25),
            since=arguments.get("since"),
            until=arguments.get("until"),
        ),
        # Campaigns
        "list_campaigns": lambda: campaigns.list_campaigns(
            _client,
            account_id=arguments["account_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "get_campaign": lambda: campaigns.get_campaign(
            _client,
            campaign_id=arguments["campaign_id"],
            fields=arguments.get("fields"),
        ),
        "get_campaign_insights": lambda: campaigns.get_campaign_insights(
            _client,
            campaign_id=arguments["campaign_id"],
            fields=arguments.get("fields"),
            date_preset=arguments.get("date_preset"),
            time_range=arguments.get("time_range"),
            time_increment=arguments.get("time_increment"),
            breakdowns=arguments.get("breakdowns"),
            level=arguments.get("level"),
            limit=arguments.get("limit", 25),
        ),
        # Ad Sets
        "list_adsets_by_account": lambda: adsets.list_adsets_by_account(
            _client,
            account_id=arguments["account_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "list_adsets_by_campaign": lambda: adsets.list_adsets_by_campaign(
            _client,
            campaign_id=arguments["campaign_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "get_adset": lambda: adsets.get_adset(
            _client,
            adset_id=arguments["adset_id"],
            fields=arguments.get("fields"),
        ),
        "get_adset_insights": lambda: adsets.get_adset_insights(
            _client,
            adset_id=arguments["adset_id"],
            fields=arguments.get("fields"),
            date_preset=arguments.get("date_preset"),
            time_range=arguments.get("time_range"),
            time_increment=arguments.get("time_increment"),
            breakdowns=arguments.get("breakdowns"),
            limit=arguments.get("limit", 25),
        ),
        # Ads
        "list_ads_by_account": lambda: ads.list_ads_by_account(
            _client,
            account_id=arguments["account_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "list_ads_by_campaign": lambda: ads.list_ads_by_campaign(
            _client,
            campaign_id=arguments["campaign_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "list_ads_by_adset": lambda: ads.list_ads_by_adset(
            _client,
            adset_id=arguments["adset_id"],
            fields=arguments.get("fields"),
            effective_status=arguments.get("effective_status"),
            limit=arguments.get("limit", 25),
        ),
        "get_ad_insights": lambda: ads.get_ad_insights(
            _client,
            ad_id=arguments["ad_id"],
            fields=arguments.get("fields"),
            date_preset=arguments.get("date_preset"),
            time_range=arguments.get("time_range"),
            time_increment=arguments.get("time_increment"),
            breakdowns=arguments.get("breakdowns"),
            limit=arguments.get("limit", 25),
        ),
        # Creatives
        "get_creative": lambda: creatives.get_creative(
            _client,
            creative_id=arguments["creative_id"],
            fields=arguments.get("fields"),
        ),
        "list_creatives_by_ad": lambda: creatives.list_creatives_by_ad(
            _client,
            ad_id=arguments["ad_id"],
            fields=arguments.get("fields"),
            limit=arguments.get("limit", 25),
        ),
        # Insights
        "get_account_insights": lambda: insights.get_account_insights(
            _client,
            account_id=arguments["account_id"],
            fields=arguments.get("fields"),
            date_preset=arguments.get("date_preset"),
            time_range=arguments.get("time_range"),
            time_increment=arguments.get("time_increment"),
            breakdowns=arguments.get("breakdowns"),
            action_breakdowns=arguments.get("action_breakdowns"),
            action_attribution_windows=arguments.get("action_attribution_windows"),
            level=arguments.get("level"),
            limit=arguments.get("limit", 25),
        ),
        "fetch_next_page": lambda: insights.fetch_next_page(
            _client,
            url=arguments["url"],
        ),
    }

    if name not in tool_handlers:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = tool_handlers[name]()
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except ValueError as e:
        return [TextContent(type="text", text=f"Validation error: {e}")]
    except Exception as e:
        # Never expose token or sensitive info in error messages
        error_msg = str(e)
        error_msg = re.sub(r"access_token=[^&\s]+", "access_token=***REDACTED***", error_msg)
        logger.error("tool_error", tool=name, error=error_msg)
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {error_msg}")]


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@app.list_resources()
async def list_resources() -> list[Resource]:
    """Register MCP resources for Meta Ads data."""
    return [
        Resource(
            uri="meta://accounts",
            name="Ad Accounts",
            description="List of all accessible Meta ad accounts with basic info.",
            mimeType="application/json",
        ),
        Resource(
            uri="meta://accounts/{account_id}/campaigns",
            name="Account Campaigns",
            description="Active campaigns for a specific ad account.",
            mimeType="application/json",
        ),
        Resource(
            uri="meta://accounts/{account_id}/summary",
            name="Account Summary",
            description="Executive summary with account details and last 7 days performance.",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Meta Ads resource by URI."""
    if _client is None:
        return json.dumps({"error": "Server not initialized"})

    uri_str = str(uri)

    if uri_str == "meta://accounts":
        return campaign_data.get_accounts_resource(_client)

    # Match meta://accounts/{id}/campaigns
    campaigns_match = re.match(r"^meta://accounts/([^/]+)/campaigns$", uri_str)
    if campaigns_match:
        account_id = campaigns_match.group(1)
        return campaign_data.get_account_campaigns_resource(_client, account_id)

    # Match meta://accounts/{id}/summary
    summary_match = re.match(r"^meta://accounts/([^/]+)/summary$", uri_str)
    if summary_match:
        account_id = summary_match.group(1)
        return campaign_data.get_account_summary_resource(_client, account_id)

    return json.dumps({"error": f"Unknown resource: {uri_str}"})


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """Register built-in analysis prompts."""
    result = []
    for prompt_data in PROMPTS.values():
        result.append(
            Prompt(
                name=prompt_data["name"],
                description=prompt_data["description"],
                arguments=[
                    PromptArgument(
                        name=arg["name"],
                        description=arg["description"],
                        required=arg.get("required", False),
                    )
                    for arg in prompt_data["arguments"]
                ],
            )
        )
    return result


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
    """Generate messages for a specific prompt."""
    if name not in PROMPTS:
        raise ValueError(f"Unknown prompt: {name}")

    messages_data = get_prompt_messages(name, arguments or {})

    messages = []
    for msg in messages_data:
        if msg["role"] == "user":
            content = msg["content"]
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            messages.append(
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=text),
                )
            )

    return GetPromptResult(
        description=PROMPTS[name]["description"],
        messages=messages,
    )


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

async def run() -> None:
    """Initialize and run the MCP server."""
    global _client

    config = load_config()
    configure_logging(log_level=config.log_level, debug=config.debug)

    _client = MetaAPIClient(config)
    logger.info("server_starting", version="0.1.0", tools=18, resources=3, prompts=len(PROMPTS))

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        if _client is not None:
            _client.close()
            logger.info("server_stopped")


def main() -> None:
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
