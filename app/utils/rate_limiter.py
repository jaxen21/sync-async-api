"""Simple in-memory rate limiter."""
import time
from collections import defaultdict
from ..config import get_settings


settings = get_settings()


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self):
        # client_ip -> (tokens, last_update)
        self.buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (settings.rate_limit_requests, time.time())
        )
    
    def check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        max_tokens = settings.rate_limit_requests
        window = settings.rate_limit_window_seconds
        refill_rate = max_tokens / window
        
        tokens, last_update = self.buckets[client_ip]
        now = time.time()
        
        # Refill tokens based on time passed
        time_passed = now - last_update
        tokens = min(max_tokens, tokens + time_passed * refill_rate)
        
        if tokens >= 1:
            # Allow request
            self.buckets[client_ip] = (tokens - 1, now)
            return True, 0
        else:
            # Deny request
            retry_after = int((1 - tokens) / refill_rate)
            return False, retry_after


# Global rate limiter instance
rate_limiter = RateLimiter()
