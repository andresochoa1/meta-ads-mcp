"""Environment-based configuration with validation."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetaAPIConfig:
    """Meta Graph API configuration."""

    access_token: str
    api_version: str = "v22.0"
    base_url: str = "https://graph.facebook.com"

    @property
    def graph_url(self) -> str:
        return f"{self.base_url}/{self.api_version}"


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting configuration."""

    max_calls_per_hour: int = 200
    burst_size: int = 50
    backoff_base: float = 1.0
    backoff_max: float = 60.0
    retry_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    max_retries: int = 3


@dataclass(frozen=True)
class ServerConfig:
    """Complete server configuration."""

    meta: MetaAPIConfig
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    log_level: str = "INFO"
    debug: bool = False


def load_config() -> ServerConfig:
    """Load configuration from environment variables.

    Required env vars:
        META_ACCESS_TOKEN: Meta Graph API access token

    Optional env vars:
        META_API_VERSION: API version (default: v22.0)
        META_RATE_LIMIT_PER_HOUR: Max API calls per hour (default: 200)
        LOG_LEVEL: Logging level (default: INFO)
        DEBUG: Enable debug mode (default: false)
    """
    access_token = os.environ.get("META_ACCESS_TOKEN")
    if not access_token:
        raise ValueError(
            "META_ACCESS_TOKEN environment variable is required. "
            "Get a token from https://developers.facebook.com/tools/explorer/"
        )

    meta_config = MetaAPIConfig(
        access_token=access_token,
        api_version=os.environ.get("META_API_VERSION", "v22.0"),
    )

    rate_limit_config = RateLimitConfig(
        max_calls_per_hour=int(os.environ.get("META_RATE_LIMIT_PER_HOUR", "200")),
    )

    return ServerConfig(
        meta=meta_config,
        rate_limit=rate_limit_config,
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        debug=os.environ.get("DEBUG", "false").lower() == "true",
    )
