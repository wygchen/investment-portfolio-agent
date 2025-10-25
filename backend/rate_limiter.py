"""
Rate Limiting Module for API Calls
Provides rate limiting for external API calls to prevent hitting rate limits
"""

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int
    time_window: int  # in seconds
    burst_limit: int = 5  # max requests in a short burst

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self):
        self.limiters: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.configs = {
            'watsonx': RateLimitConfig(max_requests=100, time_window=3600, burst_limit=10),  # 100 requests per hour
            'finnhub': RateLimitConfig(max_requests=60, time_window=60, burst_limit=5),      # 60 requests per minute
            'alpha_vantage': RateLimitConfig(max_requests=5, time_window=60, burst_limit=2), # 5 requests per minute
            'newsapi': RateLimitConfig(max_requests=1000, time_window=3600, burst_limit=20), # 1000 requests per hour
            'yahoo_finance': RateLimitConfig(max_requests=2000, time_window=3600, burst_limit=50), # 2000 requests per hour
        }
    
    async def wait_if_needed(self, api_name: str) -> bool:
        """Wait if rate limit would be exceeded, return True if request can proceed"""
        if api_name not in self.configs:
            logger.warning(f"No rate limit config for {api_name}")
            return True
            
        config = self.configs[api_name]
        now = time.time()
        
        # Clean old requests outside the time window
        request_times = self.limiters[api_name]['requests']
        while request_times and now - request_times[0] > config.time_window:
            request_times.popleft()
        
        # Check if we're at the limit
        if len(request_times) >= config.max_requests:
            # Calculate wait time
            oldest_request = request_times[0]
            wait_time = config.time_window - (now - oldest_request) + 1
            
            if wait_time > 0:
                logger.info(f"Rate limit reached for {api_name}, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                return await self.wait_if_needed(api_name)  # Recursive check after waiting
        
        # Record this request
        request_times.append(now)
        return True
    
    async def check_burst_limit(self, api_name: str) -> bool:
        """Check if burst limit is exceeded"""
        if api_name not in self.configs:
            return True
            
        config = self.configs[api_name]
        now = time.time()
        
        # Clean old burst requests (last 10 seconds)
        burst_times = self.limiters[api_name]['burst']
        while burst_times and now - burst_times[0] > 10:
            burst_times.popleft()
        
        # Check burst limit
        if len(burst_times) >= config.burst_limit:
            logger.warning(f"Burst limit exceeded for {api_name}, waiting...")
            await asyncio.sleep(1)
            return await self.check_burst_limit(api_name)
        
        # Record this burst request
        burst_times.append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_api_call(api_name: str) -> bool:
    """
    Rate limit an API call. Call this before making external API calls.
    
    Args:
        api_name: Name of the API ('watsonx', 'finnhub', 'alpha_vantage', etc.)
        
    Returns:
        bool: True if the call can proceed, False if rate limited
    """
    try:
        # Check burst limit first
        if not await rate_limiter.check_burst_limit(api_name):
            return False
        
        # Check main rate limit
        if not await rate_limiter.wait_if_needed(api_name):
            return False
        
        return True
    except Exception as e:
        logger.error(f"Rate limiting error for {api_name}: {e}")
        return True  # Allow request if rate limiter fails

def get_rate_limit_status(api_name: str) -> Dict[str, int]:
    """Get current rate limit status for an API"""
    if api_name not in rate_limiter.configs:
        return {"error": "Unknown API"}
    
    config = rate_limiter.configs[api_name]
    now = time.time()
    
    # Clean old requests
    request_times = rate_limiter.limiters[api_name]['requests']
    while request_times and now - request_times[0] > config.time_window:
        request_times.popleft()
    
    return {
        "current_requests": len(request_times),
        "max_requests": config.max_requests,
        "time_window": config.time_window,
        "remaining_requests": max(0, config.max_requests - len(request_times))
    }

