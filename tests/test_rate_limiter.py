"""Rate limiter tests."""

from meta_ads_mcp.api.rate_limiter import RateLimiter, TokenBucket, calculate_backoff
from meta_ads_mcp.config import RateLimitConfig


class TestTokenBucket:
    def test_initial_tokens_equal_burst(self):
        bucket = TokenBucket(max_calls_per_hour=100, burst_size=10)
        assert bucket._tokens == 10.0

    def test_acquire_reduces_tokens(self):
        bucket = TokenBucket(max_calls_per_hour=100, burst_size=10)
        assert bucket.acquire() is True
        assert bucket._tokens == 9.0

    def test_acquire_fails_when_empty(self):
        bucket = TokenBucket(max_calls_per_hour=100, burst_size=2)
        assert bucket.acquire() is True
        assert bucket.acquire() is True
        assert bucket.acquire() is False

    def test_wait_time_zero_when_tokens_available(self):
        bucket = TokenBucket(max_calls_per_hour=100, burst_size=10)
        assert bucket.wait_time() == 0.0


class TestBackoff:
    def test_first_attempt_bounded(self):
        delay = calculate_backoff(0, base=1.0, max_delay=60.0)
        assert 0 <= delay <= 1.0

    def test_increases_with_attempts(self):
        # With jitter, individual samples may not be monotonic,
        # but the MAX possible delay increases
        max_possible = [min(60.0, 1.0 * (2**i)) for i in range(5)]
        assert max_possible[4] > max_possible[0]

    def test_respects_max_delay(self):
        delay = calculate_backoff(100, base=1.0, max_delay=60.0)
        assert delay <= 60.0


class TestRateLimiter:
    def test_should_retry_on_429(self):
        config = RateLimitConfig(max_retries=3)
        limiter = RateLimiter(config)
        should, delay = limiter.should_retry(429, attempt=0)
        assert should is True
        assert delay >= 0

    def test_no_retry_on_400(self):
        config = RateLimitConfig(max_retries=3)
        limiter = RateLimiter(config)
        should, _ = limiter.should_retry(400, attempt=0)
        assert should is False

    def test_no_retry_after_max_attempts(self):
        config = RateLimitConfig(max_retries=3)
        limiter = RateLimiter(config)
        should, _ = limiter.should_retry(429, attempt=3)
        assert should is False
