# meta-ads-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/andresochoa1/meta-ads-mcp/tests.yml?label=tests)](https://github.com/andresochoa1/meta-ads-mcp/actions)

**Security-first MCP server for Meta (Facebook/Instagram) Ads API.**

---

## Why this exists

Existing MCP integrations for Meta Ads have significant security gaps: no SSRF protection on pagination URLs, access tokens leaking into logs and error messages, no rate limiting, and no input validation. This server is built from scratch with zero-trust principles. Every outbound request is validated against a domain allowlist, every log line is automatically redacted, and every ID is pattern-checked before it touches the API.

## Features

- **18 tools** covering accounts, campaigns, ad sets, ads, creatives, and insights
- **3 MCP resources** for campaign metadata and account summaries
- **5 built-in MCP prompts** for common analysis workflows (performance analysis, underperformer detection, budget efficiency, creative fatigue, daily monitoring)
- **Zero-trust security** -- SSRF protection via domain allowlist, token redaction in all logs and errors, input validation on all IDs
- **Rate limiting** with token bucket algorithm and exponential backoff with jitter
- **Structured logging** with automatic secret redaction (structlog)
- **Built on Meta's Graph API** via `httpx` with zero-trust HTTP controls

## Quick Start

### Prerequisites

- Python 3.11 or higher
- A Meta Developer account with an app that has `ads_read` permission
- A valid Meta Graph API access token

### Install

```bash
pip install meta-ads-mcp
```

### Get your access token

1. Go to [Meta Developer Tools](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Generate a token with `ads_read` permission
4. For production use, exchange for a long-lived token

### Set environment variable

```bash
export META_ACCESS_TOKEN=your_token_here
```

### Configure in Claude Desktop

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "meta-ads-mcp",
      "env": {
        "META_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Configure in Claude Code

Add to your project or global `.claude/settings.json`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "meta-ads-mcp",
      "env": {
        "META_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Configuration

All configuration is via environment variables. The access token is never accepted as a CLI argument.

| Variable | Required | Default | Description |
|---|---|---|---|
| `META_ACCESS_TOKEN` | Yes | -- | Meta Graph API access token |
| `META_API_VERSION` | No | `v22.0` | Graph API version |
| `META_RATE_LIMIT_PER_HOUR` | No | `200` | Maximum API calls per hour |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG` | No | `false` | Enable debug mode with console rendering |

## Available Tools

### Accounts (3)

| Tool | Description | Required Parameters |
|---|---|---|
| `list_ad_accounts` | List all accessible ad accounts with name, ID, status, currency, balance, and spend | -- |
| `get_ad_account_details` | Get detailed info for a specific ad account | `account_id` |
| `get_ad_account_activities` | Get the activity log for an ad account | `account_id` |

### Campaigns (3)

| Tool | Description | Required Parameters |
|---|---|---|
| `list_campaigns` | List campaigns for an account, filterable by status | `account_id` |
| `get_campaign` | Get campaign details including objective, budget, and schedule | `campaign_id` |
| `get_campaign_insights` | Get performance metrics with date presets, breakdowns, and time increments | `campaign_id` |

### Ad Sets (4)

| Tool | Description | Required Parameters |
|---|---|---|
| `list_adsets_by_account` | List ad sets for an account, filterable by status | `account_id` |
| `list_adsets_by_campaign` | List ad sets for a specific campaign | `campaign_id` |
| `get_adset` | Get ad set details including targeting, budget, and optimization goal | `adset_id` |
| `get_adset_insights` | Get performance metrics for a specific ad set | `adset_id` |

### Ads (4)

| Tool | Description | Required Parameters |
|---|---|---|
| `list_ads_by_account` | List ads for an account, filterable by status | `account_id` |
| `list_ads_by_campaign` | List ads for a specific campaign | `campaign_id` |
| `list_ads_by_adset` | List ads for a specific ad set | `adset_id` |
| `get_ad_insights` | Get performance metrics for a specific ad | `ad_id` |

### Creatives (2)

| Tool | Description | Required Parameters |
|---|---|---|
| `get_creative` | Get creative details including title, body, image URL, and object story spec | `creative_id` |
| `list_creatives_by_ad` | List creatives associated with a specific ad | `ad_id` |

### Insights (2)

| Tool | Description | Required Parameters |
|---|---|---|
| `get_account_insights` | Get comprehensive account-level insights with all breakdown and attribution options | `account_id` |
| `fetch_next_page` | Fetch the next page of results from a pagination URL (SSRF-validated) | `url` |

### Common Optional Parameters

Most tools support these optional parameters:

| Parameter | Type | Description |
|---|---|---|
| `fields` | `string[]` | Specific fields to retrieve |
| `effective_status` | `string[]` | Filter by status (`ACTIVE`, `PAUSED`, `ARCHIVED`, etc.) |
| `limit` | `integer` | Maximum results per page (default: 25) |
| `date_preset` | `string` | Date range preset (`today`, `yesterday`, `last_7d`, `last_30d`, `this_month`, `last_month`) |
| `time_range` | `object` | Custom date range with `since` and `until` (YYYY-MM-DD) |
| `time_increment` | `string` | Time granularity (`1`, `7`, `28`, `monthly`, `all_days`) |
| `breakdowns` | `string[]` | Breakdown dimensions (`age`, `gender`, `country`, `placement`, etc.) |

## Available Resources

| URI | Name | Description |
|---|---|---|
| `meta://accounts` | Ad Accounts | List of all accessible ad accounts with basic info |
| `meta://accounts/{account_id}/campaigns` | Account Campaigns | Active campaigns for a specific account |
| `meta://accounts/{account_id}/summary` | Account Summary | Executive summary with account details and last 7 days performance |

## Available Prompts

| Prompt | Description | Required Arguments |
|---|---|---|
| `analyze-campaign-performance` | Analyze metrics and provide optimization recommendations | `campaign_id` |
| `find-underperformers` | Identify ads performing below CPA/ROAS targets | `account_id` |
| `daily-monitoring-report` | Generate a daily health report with spend pacing and anomaly detection | `account_id` |
| `budget-efficiency-check` | Evaluate budget distribution vs. ROAS performance | `account_id` |
| `creative-fatigue-audit` | Detect ads with declining CTR, rising frequency, and stale engagement | `account_id` |

## Security Model

This server implements a zero-trust security architecture. Key protections include:

- **SSRF protection** -- All outbound URLs (including pagination) are validated against a strict domain allowlist (`graph.facebook.com`, `www.facebook.com`)
- **Token management** -- Access tokens are loaded from environment variables only, never accepted as CLI arguments, and never appear in logs or error messages
- **Input validation** -- All Meta Ads IDs are validated against expected patterns before API calls
- **Log redaction** -- A structlog processor automatically redacts sensitive fields (`access_token`, `secret`, `password`, `key`, `authorization`) from all log output
- **No redirects** -- HTTP client is configured to never follow redirects, preventing redirect-based SSRF
- **HTTPS only** -- All requests are validated to use HTTPS

For the complete security documentation, see [SECURITY.md](SECURITY.md).

## Development

### Clone and install

```bash
git clone https://github.com/andresochoa1/meta-ads-mcp.git
cd meta-ads-mcp
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Lint

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

### Project structure

```
src/meta_ads_mcp/
  server.py          # MCP server entry point, tool/resource/prompt registration
  config.py          # Environment-based configuration with validation
  security.py        # SSRF protection, token redaction, input validation
  api/
    client.py        # Secure Meta Graph API client
    rate_limiter.py  # Token bucket + exponential backoff
    pagination.py    # Cursor-based pagination with URL validation
  tools/
    accounts.py      # Ad account tools
    campaigns.py     # Campaign tools
    adsets.py        # Ad set tools
    ads.py           # Ad tools
    creatives.py     # Creative tools
    insights.py      # Insights and pagination tools
  prompts/
    analysis.py      # Built-in analysis prompts
  resources/
    campaign_data.py # MCP resource implementations
tests/
  test_security.py   # Security layer tests
  test_rate_limiter.py # Rate limiter tests
  test_pagination.py # Pagination tests
```

## License

[MIT](LICENSE) -- Copyright (c) 2026 Andres Ochoa

## Contributing

Contributions are welcome. Please follow these guidelines:

1. **Fork** the repository and create a feature branch
2. **Write tests** for any new functionality
3. **Run the full test suite** (`pytest`) and linter (`ruff check`) before submitting
4. **Follow the existing code style** -- the project uses ruff for formatting and linting
5. **Security-sensitive changes** require extra review. If your change touches `security.py`, `client.py`, or URL handling, please explain the security implications in your PR description
6. **Open an issue first** for large changes to discuss the approach before implementation

### Reporting security vulnerabilities

Please do **not** open a public issue for security vulnerabilities. Instead, see [SECURITY.md](SECURITY.md) for responsible disclosure instructions.
