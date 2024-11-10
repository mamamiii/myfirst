from functools import wraps
from datetime import datetime, timedelta
import hashlib

class CacheManager:
    _cache = {}
    
    @staticmethod
    def cache_key(func, *args, **kwargs):
        # Create a unique cache key based on function name and arguments
        key_parts = [func.__name__]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    @classmethod
    def cached(cls, timeout_seconds):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = cls.cache_key(func, *args, **kwargs)
                
                # Check if cached data exists and is still valid
                if cache_key in cls._cache:
                    data, timestamp = cls._cache[cache_key]
                    if datetime.now() - timestamp < timedelta(seconds=timeout_seconds):
                        return data

                # Get fresh data
                result = func(*args, **kwargs)
                cls._cache[cache_key] = (result, datetime.now())
                return result
            return wrapper
        return decorator
