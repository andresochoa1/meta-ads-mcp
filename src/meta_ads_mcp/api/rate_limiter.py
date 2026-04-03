"""Token bucket rate limiter with exponential backoff and jitter."""

import random
import time
from dataclasses import dataclass, field

import structlog

from meta_ads_mcp.config import RateLimitConfig

logger = structlog.get_logger()


@dataclass
class TokenBucket:
    """Token bucket rate limiter.

    Allows burst traffic up to `burst_size` while maintaining
    a sustainable rate of `max_calls_per_hour`.
    """

    max_calls_per_hour: int = 200
    burst_size: int = 50
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self._tokens = float(self.burst_size)
        self._last_refill = time.monotonic()

    @property
    def _refill_rate(self) -> float:
        """Tokens added per second."""
        return self.max_calls_per_hour / 3600.0

    def _refill(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * self._refill_rate
        self._tokens = min(self.burst_size, self._tokens + new_tokens)
        self._last_refill = now

    def acquire(self) -> bool:
        """Try to acquire a token. Returns True if allowed."""
        self._refill()
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def wait_time(self) -> float:
        """Seconds to wait before the next token is available."""
        self._refill()
        if self._tokens >= 1.0:
            return 0.0
        deficit = 1.0 - self._tokens
        return deficit / self._refill_rate


def calculate_backoff(
    attempt: int,
    base: float = 1.0,
    max_delay: float = 60.0,
) -> float:
    """Calculate exponential backoff with jitter.

    Uses "full jitter" strategy: random(0, min(max_delay, base * 2^attempt))
    This prevents thundering herd on rate limit recovery.
    """
    delay = min(max_delay, base * (2**attempt))
    jittered = random.uniform(0, delay)  # noqa: S311
    return jittered


class RateLimiter:
    """Rate limiter combining token bucket with retry logic."""

    def __init__(self, config: RateLimitConfig) -> None:
        self._config = config
        self._bucket = TokenBucket(
            max_calls_per_hour=config.max_calls_per_hour,
            burst_size=config.burst_size,
        )

    def acquire_or_wait(self) -> None:
        """Acquire a rate limit token, waiting if necessary."""
        if self._bucket.acquire():
            return

        wait = self._bucket.wait_time()
        logger.info("rate_limit_wait", wait_seconds=round(wait, 2))
        time.sleep(wait)

        # Try again after waiting
        if not self._bucket.acquire():
            raise RuntimeError("Rate limiter failed to acquire token after waiting")

    def should_retry(self, status_code: int, attempt: int) -> tuple[bool, float]:
        """Determine if a request should be retried.

        Returns:
            Tuple of (should_retry, wait_seconds).
        """
        if attempt >= self._config.max_retries:
            return False, 0.0

        if status_code not in self._config.retry_status_codes:
            return False, 0.0

        delay = calculate_backoff(
            attempt,
            base=self._config.backoff_base,
            max_delay=self._config.backoff_max,
        )

        logger.info(
            "retry_scheduled",
            attempt=attempt + 1,
            max_retries=self._config.max_retries,
            status_code=status_code,
            delay_seconds=round(delay, 2),
        )

        return True, delay
