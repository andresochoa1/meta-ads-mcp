"""Built-in MCP prompts for Meta Ads analysis.

These prompts provide pre-built analysis workflows that LLMs can use
to perform common Meta Ads optimization tasks.
"""

from __future__ import annotations

from typing import Any

PROMPTS: dict[str, dict[str, Any]] = {
    "analyze-campaign-performance": {
        "name": "analyze-campaign-performance",
        "description": (
            "Analyze a campaign's performance metrics and provide actionable "
            "recommendations for optimization."
        ),
        "arguments": [
            {
                "name": "campaign_id",
                "description": "The campaign ID to analyze",
                "required": True,
            },
            {
                "name": "date_range",
                "description": "Date range (e.g., last_7d, last_30d)",
                "required": False,
            },
        ],
    },
    "find-underperformers": {
        "name": "find-underperformers",
        "description": (
            "Identify ads and ad sets performing below target thresholds. "
            "Flags high-spend / low-ROAS combinations."
        ),
        "arguments": [
            {
                "name": "account_id",
                "description": "Ad account ID",
                "required": True,
            },
            {
                "name": "cpa_target",
                "description": "Target cost per action",
                "required": False,
            },
            {
                "name": "roas_target",
                "description": "Target return on ad spend",
                "required": False,
            },
        ],
    },
    "daily-monitoring-report": {
        "name": "daily-monitoring-report",
        "description": (
            "Generate a daily health report for an ad account covering "
            "spend pacing, CPM trends, and delivery issues."
        ),
        "arguments": [
            {
                "name": "account_id",
                "description": "Ad account ID",
                "required": True,
            },
        ],
    },
    "budget-efficiency-check": {
        "name": "budget-efficiency-check",
        "description": (
            "Evaluate budget distribution across campaigns and ad sets "
            "vs their ROAS performance. Identifies misallocations."
        ),
        "arguments": [
            {
                "name": "account_id",
                "description": "Ad account ID",
                "required": True,
            },
        ],
    },
    "creative-fatigue-audit": {
        "name": "creative-fatigue-audit",
        "description": (
            "Detect ads showing signs of creative fatigue: declining CTR, "
            "rising frequency, stale engagement."
        ),
        "arguments": [
            {
                "name": "account_id",
                "description": "Ad account ID",
                "required": True,
            },
            {
                "name": "days",
                "description": "Number of days to analyze (default: 14)",
                "required": False,
            },
        ],
    },
}


def get_prompt_messages(prompt_name: str, arguments: dict[str, str]) -> list[dict[str, Any]]:
    """Generate the message sequence for a prompt.

    Each prompt generates a system + user message pair that instructs
    the LLM on what tools to call and how to analyze the results.
    """
    if prompt_name == "analyze-campaign-performance":
        campaign_id = arguments.get("campaign_id", "")
        date_range = arguments.get("date_range", "last_7d")
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Analyze the performance of campaign {campaign_id} "
                        f"over the {date_range} period.\n\n"
                        "Steps:\n"
                        "1. Use get_campaign to get campaign details\n"
                        "2. Use get_campaign_insights with the date range to get metrics\n"
                        "3. Analyze CTR, CPC, CPM, and conversion trends\n"
                        "4. Provide specific, actionable recommendations\n\n"
                        "Focus on: cost efficiency, audience fatigue signals, "
                        "and budget utilization."
                    ),
                },
            }
        ]

    if prompt_name == "find-underperformers":
        account_id = arguments.get("account_id", "")
        cpa_target = arguments.get("cpa_target", "not specified")
        roas_target = arguments.get("roas_target", "not specified")
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Find underperforming ads in account {account_id}.\n\n"
                        f"CPA target: {cpa_target}\n"
                        f"ROAS target: {roas_target}\n\n"
                        "Steps:\n"
                        "1. Use get_account_insights with level='ad' and last_7d\n"
                        "2. Identify ads with CPA above target or ROAS below target\n"
                        "3. Flag ads with high spend but low conversions\n"
                        "4. Recommend: pause, adjust, or scale each ad\n\n"
                        "Present results as a ranked table from worst to best performer."
                    ),
                },
            }
        ]

    if prompt_name == "daily-monitoring-report":
        account_id = arguments.get("account_id", "")
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Generate a daily monitoring report for account {account_id}.\n\n"
                        "Steps:\n"
                        "1. Use get_account_insights with date_preset='today' for today's data\n"
                        "2. Use get_account_insights with date_preset='yesterday' for comparison\n"
                        "3. Use list_campaigns to check active campaign count\n"
                        "4. Report on: spend pacing, CPM changes, CTR trends, "
                        "delivery anomalies\n\n"
                        "Flag any metric that changed more than 20% from yesterday."
                    ),
                },
            }
        ]

    if prompt_name == "budget-efficiency-check":
        account_id = arguments.get("account_id", "")
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Evaluate budget efficiency for account {account_id}.\n\n"
                        "Steps:\n"
                        "1. Use list_campaigns to get all active campaigns with budgets\n"
                        "2. Use get_account_insights with level='campaign' and last_7d\n"
                        "3. Calculate ROAS and CPA per campaign\n"
                        "4. Identify campaigns where budget share doesn't match "
                        "performance share\n\n"
                        "Recommend specific budget reallocations with amounts."
                    ),
                },
            }
        ]

    if prompt_name == "creative-fatigue-audit":
        account_id = arguments.get("account_id", "")
        days = arguments.get("days", "14")
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Audit creative fatigue for account {account_id} "
                        f"over the last {days} days.\n\n"
                        "Steps:\n"
                        "1. Use get_account_insights with level='ad', time_increment='1', "
                        f"and a {days}-day time range\n"
                        "2. For each ad, plot the CTR and frequency trend\n"
                        "3. Flag ads where: frequency > 3, CTR declining >15%, "
                        "or spend increasing while conversions flat\n"
                        "4. Recommend creative refresh priorities\n\n"
                        "Rank by urgency: critical / warning / healthy."
                    ),
                },
            }
        ]

    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Unknown prompt: {prompt_name}",
            },
        }
    ]
