"""Zero-trust security layer: token management, URL validation, log redaction."""

import re
from urllib.parse import urlparse

import structlog

# Domain allowlist — ONLY Meta's Graph API
ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "graph.facebook.com",
        "www.facebook.com",
    }
)

# Regex for valid Meta Ads IDs
ID_PATTERN = re.compile(r"^(act_)?\d+$")

# Fields that must NEVER appear in logs
SENSITIVE_FIELDS: frozenset[str] = frozenset(
    {
        "access_token",
        "token",
        "secret",
        "password",
        "key",
        "authorization",
        "appsecret_proof",
    }
)


def validate_url(url: str) -> str:
    """Validate that a URL points to an allowed Meta API domain.

    Raises:
        ValueError: If the URL's domain is not in the allowlist.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname

    if hostname is None:
        raise ValueError("Invalid URL: no hostname found")

    if hostname not in ALLOWED_DOMAINS:
        raise ValueError(
            f"URL blocked: domain '{hostname}' is not in the allowlist. "
            f"Only {', '.join(sorted(ALLOWED_DOMAINS))} are allowed."
        )

    if parsed.scheme not in ("https",):
        raise ValueError(f"URL blocked: only HTTPS is allowed, got '{parsed.scheme}'")

    return url


def validate_id(value: str, name: str = "id") -> str:
    """Validate that a Meta Ads ID matches the expected pattern.

    Valid formats: '123456789', 'act_123456789'

    Raises:
        ValueError: If the ID doesn't match the expected pattern.
    """
    if not ID_PATTERN.match(value):
        raise ValueError(
            f"Invalid {name}: '{value}'. Expected numeric ID or 'act_' prefix + numeric ID."
        )
    return value


def redact_sensitive_params(params: dict) -> dict:
    """Create a copy of params with sensitive values redacted.

    Used for safe logging — never log raw params that may contain tokens.
    """
    redacted = {}
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted


def _structlog_redact_processor(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Structlog processor that automatically redacts sensitive fields."""
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            event_dict[key] = "***REDACTED***"
        elif isinstance(event_dict[key], dict):
            event_dict[key] = redact_sensitive_params(event_dict[key])
    return event_dict


def configure_logging(log_level: str = "INFO", debug: bool = False) -> None:
    """Configure structlog with automatic secret redaction."""
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _structlog_redact_processor,  # Always redact before rendering
    ]

    if debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
