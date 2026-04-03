# Security Policy

## Security Model Overview

`meta-ads-mcp` implements a **zero-trust architecture** for interacting with the Meta Graph API. The server assumes that all inputs are potentially malicious and validates everything before it reaches the API or appears in any output.

The security model is built on six pillars:

1. Token management
2. SSRF protection
3. Input validation
4. Log redaction
5. Rate limiting
6. Dependency minimalism

## Token Management

Access tokens are the most sensitive asset in this system. The server enforces strict controls:

- **Environment variables only** -- Tokens are loaded exclusively from the `META_ACCESS_TOKEN` environment variable. They are never accepted as CLI arguments, configuration file values, or tool parameters.
- **Never logged** -- The structlog redaction processor ensures tokens never appear in log output, regardless of log level.
- **Never in error messages** -- All error handlers use regex replacement to strip `access_token=` patterns from any error string before it reaches the user.
- **Never in URLs** -- Tokens are passed as request parameters, not embedded in URLs that could leak through referrer headers or logs.
- **No redirect following** -- The HTTP client is configured with `follow_redirects=False` to prevent tokens from being sent to unexpected hosts via redirect chains.

## SSRF Protection

Server-Side Request Forgery (SSRF) is a critical risk for any MCP server that makes outbound HTTP requests. This server implements defense in depth:

### Domain Allowlist

All outbound requests are validated against a strict allowlist:

```
graph.facebook.com
www.facebook.com
```

No other domains are permitted. This applies to:

- Standard API requests (node and edge fetches)
- Pagination URLs (the `fetch_next_page` tool validates the URL before fetching)
- Any URL constructed from user input

### URL Validation Rules

The `validate_url()` function enforces:

1. **Valid hostname** -- The URL must have a parseable hostname
2. **Allowlist match** -- The hostname must be in the domain allowlist
3. **HTTPS only** -- Only the `https` scheme is permitted

### No Redirect Following

The HTTP client is explicitly configured to reject redirects. This prevents an attacker from providing a Meta API URL that redirects to an internal or malicious host.

## Input Validation

All identifiers are validated before they are used in API requests:

### ID Pattern Matching

Meta Ads IDs must match the pattern `^(act_)?\d+$`:

- Pure numeric: `123456789`
- Account prefix: `act_123456789`

Any ID that does not match this pattern is rejected with a `ValueError` before an API call is made. This prevents injection of path traversal sequences, query parameters, or other malicious payloads through ID fields.

### Parameter Sanitization

The API client's `_prepare_params()` method handles type conversions safely:

- Lists are comma-joined or JSON-encoded depending on the field
- Booleans are converted to string literals
- `None` values are stripped

No raw user input is interpolated into URLs or query strings without processing.

## Log Redaction

All logging uses `structlog` with a custom redaction processor that runs before any log renderer.

### Redacted Fields

The following field names trigger automatic redaction:

- `access_token`
- `token`
- `secret`
- `password`
- `key`
- `authorization`
- `appsecret_proof`

The redaction is case-insensitive and matches on substrings (e.g., a field named `my_access_token_value` is also redacted).

### How It Works

The `_structlog_redact_processor` runs in the structlog processing chain before the renderer. It:

1. Iterates all keys in the event dictionary
2. Replaces values of sensitive keys with `***REDACTED***`
3. Recursively redacts nested dictionaries

This means that even if a developer accidentally logs a full parameter dictionary, the token is redacted before it reaches stdout/stderr.

## Rate Limiting

The server implements a two-layer rate limiting strategy to stay within Meta's API limits and handle errors gracefully.

### Token Bucket

The primary rate limiter uses a token bucket algorithm:

- **Sustainable rate**: Configurable calls per hour (default: 200)
- **Burst capacity**: Configurable burst size (default: 50)
- **Automatic refill**: Tokens are replenished based on elapsed time

When the bucket is empty, the server waits for a token to become available rather than failing immediately.

### Exponential Backoff with Jitter

For retryable HTTP errors (429, 500, 502, 503, 504), the server uses exponential backoff with full jitter:

```
delay = random(0, min(max_delay, base * 2^attempt))
```

The "full jitter" strategy prevents thundering herd effects when multiple requests hit a rate limit simultaneously.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `META_RATE_LIMIT_PER_HOUR` | 200 | Maximum API calls per hour |
| Burst size | 50 | Maximum concurrent burst |
| Backoff base | 1.0s | Initial backoff delay |
| Backoff max | 60.0s | Maximum backoff delay |
| Max retries | 3 | Maximum retry attempts per request |

## Dependency Minimalism

The server has only **4 production dependencies**, all well-established and widely audited:

| Dependency | Purpose | Weekly Downloads |
|---|---|---|
| `mcp` | MCP protocol implementation | Core protocol |
| `facebook-business` | Meta's official Graph API SDK | Official SDK |
| `structlog` | Structured logging with processors | 5M+ |
| `httpx` | Modern HTTP client | 30M+ |

No utility libraries, no frameworks, no transitive dependency trees. This minimizes the attack surface and reduces supply chain risk.

## Comparison with Existing MCPs

| Security Feature | meta-ads-mcp | Typical Meta MCP |
|---|---|---|
| SSRF protection (domain allowlist) | Yes | No |
| Pagination URL validation | Yes | No |
| Token redaction in logs | Yes (structlog processor) | No |
| Token redaction in errors | Yes (regex replacement) | No |
| Input ID validation | Yes (pattern matching) | No |
| Rate limiting | Yes (token bucket + backoff) | No |
| No redirect following | Yes | Not configured |
| HTTPS enforcement | Yes | Implicit only |
| Structured logging | Yes (structlog + JSON) | print/basic logging |
| Dependency count | 4 | 5-15+ |

## Reporting Vulnerabilities

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Instead, report it privately:

1. **Email**: Send details to the repository owner via the contact information on the [GitHub profile](https://github.com/Andresochoa88)
2. **GitHub Security Advisories**: Use the [private vulnerability reporting](https://github.com/Andresochoa88/meta-ads-mcp/security/advisories/new) feature

Please include:

- A description of the vulnerability
- Steps to reproduce
- The potential impact
- Any suggested fix (optional)

We aim to acknowledge reports within 48 hours and provide a fix within 7 days for critical issues.

## Security Updates

Security patches are released as soon as possible after discovery. Watch the repository releases for notifications.
