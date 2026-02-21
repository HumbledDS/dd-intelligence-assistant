"""
Rate limiter implementation for data collection APIs.
Uses sliding window algorithm with Redis backend for distributed rate limiting.
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int
    window_seconds: int
    burst_size: int = 0  # Allow burst requests
    cost_per_request: int = 1  # Cost weight for different request types

class RateLimiter:
    """
    Distributed rate limiter using Redis with sliding window algorithm.
    Supports multiple rate limit tiers and burst handling.
    """
    
    def __init__(self, redis_client: redis.Redis, config: RateLimitConfig):
        self.redis = redis_client
        self.config = config
        self.logger = logger.bind(component="rate_limiter")
        
    async def is_allowed(self, key: str, cost: int = 1) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier for the rate limit (e.g., API key, IP)
            cost: Cost of this request (default: 1)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            current_time = time.time()
            window_start = current_time - self.config.window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove expired entries (older than window)
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Get current score (sum of costs)
            pipe.zrange(key, 0, -1, withscores=True)
            
            results = await pipe.execute()
            
            current_count = results[1]
            current_score = sum(score for _, score in results[2]) if results[2] else 0
            
            # Check if request would exceed limits
            if current_score + cost > self.config.max_requests:
                remaining_time = await self._get_remaining_time(key, window_start)
                
                self.logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    current_score=current_score,
                    cost=cost,
                    limit=self.config.max_requests,
                    remaining_time=remaining_time
                )
                
                return False, {
                    "allowed": False,
                    "current_score": current_score,
                    "limit": self.config.max_requests,
                    "remaining_time": remaining_time,
                    "retry_after": remaining_time
                }
            
            # Add current request to window
            await self.redis.zadd(key, {str(current_time): cost})
            
            # Set expiration for cleanup
            await self.redis.expire(key, self.config.window_seconds * 2)
            
            # Calculate remaining capacity
            remaining_requests = self.config.max_requests - (current_score + cost)
            
            self.logger.debug(
                "Request allowed",
                key=key,
                cost=cost,
                remaining_requests=remaining_requests
            )
            
            return True, {
                "allowed": True,
                "current_score": current_score + cost,
                "limit": self.config.max_requests,
                "remaining_requests": remaining_requests,
                "reset_time": current_time + self.config.window_seconds
            }
            
        except Exception as e:
            self.logger.error("Rate limiter error", key=key, error=str(e))
            # Fail open - allow request if rate limiter fails
            return True, {"allowed": True, "error": str(e)}
    
    async def _get_remaining_time(self, key: str, window_start: float) -> float:
        """Calculate remaining time until rate limit resets"""
        try:
            # Find the oldest request in the current window
            oldest_requests = await self.redis.zrangebyscore(
                key, window_start, '+inf', start=0, num=1, withscores=True
            )
            
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                return self.config.window_seconds - (time.time() - oldest_time)
            
            return 0
        except Exception as e:
            self.logger.error("Error calculating remaining time", error=str(e))
            return 0
    
    async def get_status(self, key: str) -> Dict[str, any]:
        """Get current rate limit status for a key"""
        try:
            current_time = time.time()
            window_start = current_time - self.config.window_seconds
            
            # Clean expired entries
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Get current count and score
            current_count = await self.redis.zcard(key)
            current_score = await self.redis.zscore(key, str(current_time)) or 0
            
            return {
                "key": key,
                "current_count": current_count,
                "current_score": current_score,
                "limit": self.config.max_requests,
                "window_seconds": self.config.window_seconds,
                "remaining_requests": max(0, self.config.max_requests - current_score),
                "reset_time": current_time + self.config.window_seconds
            }
        except Exception as e:
            self.logger.error("Error getting rate limit status", key=key, error=str(e))
            return {"error": str(e)}
    
    async def reset(self, key: str) -> bool:
        """Reset rate limit for a specific key"""
        try:
            await self.redis.delete(key)
            self.logger.info("Rate limit reset", key=key)
            return True
        except Exception as e:
            self.logger.error("Error resetting rate limit", key=key, error=str(e))
            return False

class RateLimitManager:
    """Manages multiple rate limiters for different APIs and tiers"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.limiters: Dict[str, RateLimiter] = {}
        self.logger = logger.bind(component="rate_limit_manager")
        
    def add_limiter(self, name: str, config: RateLimitConfig):
        """Add a new rate limiter"""
        self.limiters[name] = RateLimiter(self.redis, config)
        self.logger.info("Added rate limiter", name=name, config=config)
    
    async def check_rate_limit(self, limiter_name: str, key: str, cost: int = 1) -> Tuple[bool, Dict[str, any]]:
        """Check rate limit using a specific limiter"""
        if limiter_name not in self.limiters:
            self.logger.warning("Rate limiter not found", name=limiter_name)
            return True, {"allowed": True, "warning": "Limiter not configured"}
        
        return await self.limiters[limiter_name].is_allowed(key, cost)
    
    async def get_all_statuses(self) -> Dict[str, Dict[str, any]]:
        """Get status for all rate limiters"""
        statuses = {}
        for name, limiter in self.limiters.items():
            # Get status for a sample key (you might want to modify this)
            statuses[name] = await limiter.get_status(f"status_check_{name}")
        return statuses
