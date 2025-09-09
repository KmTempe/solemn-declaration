# redis_helper.py
import os
import json
import redis
from datetime import datetime, timedelta
from functools import wraps
import hashlib
from typing import Optional, Any, Union

class RedisHelper:
    def __init__(self):
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client: Optional[redis.Redis] = None
        self.redis_available = False
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection with fallback"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            if self.redis_client:
                self.redis_client.ping()
                self.redis_available = True
                print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}. Falling back to in-memory storage.")
            self.redis_available = False
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_available and self.redis_client is not None
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get value from Redis with fallback"""
        if not self.is_available() or not self.redis_client:
            return default
        try:
            result = self.redis_client.get(key)
            return str(result) if result is not None else default
        except Exception:
            return default
    
    def set(self, key: str, value: Union[str, int], ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        if not self.is_available() or not self.redis_client:
            return False
        try:
            result = self.redis_client.set(key, value, ex=ex)
            return bool(result)
        except Exception:
            return False
    
    def hget(self, name: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get hash field from Redis"""
        if not self.is_available() or not self.redis_client:
            return default
        try:
            result = self.redis_client.hget(name, key)
            return str(result) if result is not None else default
        except Exception:
            return default
    
    def hset(self, name: str, mapping: dict) -> bool:
        """Set hash fields in Redis"""
        if not self.is_available() or not self.redis_client:
            return False
        try:
            result = self.redis_client.hset(name, mapping=mapping)
            return bool(result)
        except Exception:
            return False
    
    def expire(self, name: str, time: int) -> bool:
        """Set expiration for Redis key"""
        if not self.is_available() or not self.redis_client:
            return False
        try:
            result = self.redis_client.expire(name, time)
            return bool(result)
        except Exception:
            return False
    
    def delete(self, *names: str) -> bool:
        """Delete keys from Redis"""
        if not self.is_available() or not self.redis_client:
            return False
        try:
            result = self.redis_client.delete(*names)
            return bool(result)
        except Exception:
            return False
    
    def exists(self, name: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_available() or not self.redis_client:
            return False
        try:
            result = self.redis_client.exists(name)
            return bool(result)
        except Exception:
            return False
    
    def incr(self, name: str, amount: int = 1) -> Optional[int]:
        """Increment value in Redis"""
        if not self.is_available() or not self.redis_client:
            return None
        try:
            result = self.redis_client.incr(name, amount)
            return int(str(result)) if result is not None else None
        except Exception:
            return None
    
    def hincrby(self, name: str, key: str, amount: int = 1) -> Optional[int]:
        """Increment hash field in Redis"""
        if not self.is_available() or not self.redis_client:
            return None
        try:
            result = self.redis_client.hincrby(name, key, amount)
            return int(str(result)) if result is not None else None
        except Exception:
            return None

# Global Redis instance
redis_helper = RedisHelper()

def cache_result(key_prefix, expiration=3600):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{key_prefix}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = redis_helper.get(cache_key)
            if cached_result:
                try:
                    return json.loads(str(cached_result))
                except json.JSONDecodeError:
                    pass
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_helper.set(cache_key, json.dumps(result), ex=expiration)
            return result
        return wrapper
    return decorator

def rate_limit(key_prefix, limit=5, window=300):
    """Decorator for rate limiting with Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier (usually IP or email)
            identifier = kwargs.get('identifier') or (args[0] if args else 'unknown')
            rate_key = f"rate_limit:{key_prefix}:{identifier}"
            
            current = redis_helper.get(rate_key)
            if current is None:
                redis_helper.set(rate_key, 1, ex=window)
                return func(*args, **kwargs)
            elif int(str(current)) < limit:
                redis_helper.incr(rate_key)
                return func(*args, **kwargs)
            else:
                from flask import abort
                abort(429)  # Too Many Requests
        return wrapper
    return decorator

def track_metric(metric_name, value=1):
    """Track application metrics in Redis"""
    hour_key = f"metrics:{metric_name}:{datetime.now().strftime('%Y-%m-%d:%H')}"
    day_key = f"metrics:{metric_name}:{datetime.now().strftime('%Y-%m-%d')}"
    
    redis_helper.incr(hour_key, value)
    redis_helper.expire(hour_key, 86400 * 7)  # Keep for 7 days
    
    redis_helper.incr(day_key, value)
    redis_helper.expire(day_key, 86400 * 30)  # Keep for 30 days
