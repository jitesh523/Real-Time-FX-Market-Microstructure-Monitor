"""Caching layer for frequently accessed data."""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from functools import lru_cache
import pickle
from loguru import logger


class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 60):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries
        """
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
        
        logger.info(f"Initialized cache with TTL={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if expired/missing
        """
        if key not in self.cache:
            return None
        
        # Check if expired
        if self._is_expired(key):
            self._remove(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.timestamps:
            return True
        
        age = (datetime.now() - self.timestamps[key]).total_seconds()
        return age > self.ttl_seconds
    
    def _remove(self, key: str):
        """Remove entry from cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        logger.info("Cache cleared")
    
    def get_statistics(self) -> Dict:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for key in self.cache.keys() if self._is_expired(key))
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self.ttl_seconds
        }


class MetricsCache:
    """Specialized cache for metrics data."""
    
    def __init__(self):
        """Initialize metrics cache."""
        self.spread_cache = SimpleCache(ttl_seconds=5)
        self.depth_cache = SimpleCache(ttl_seconds=5)
        self.volatility_cache = SimpleCache(ttl_seconds=10)
        
        logger.info("Initialized Metrics Cache")
    
    def get_spread_metrics(self, symbol: str) -> Optional[Dict]:
        """Get cached spread metrics."""
        return self.spread_cache.get(f"spread_{symbol}")
    
    def set_spread_metrics(self, symbol: str, metrics: Dict):
        """Cache spread metrics."""
        self.spread_cache.set(f"spread_{symbol}", metrics)
    
    def get_depth_metrics(self, symbol: str) -> Optional[Dict]:
        """Get cached depth metrics."""
        return self.depth_cache.get(f"depth_{symbol}")
    
    def set_depth_metrics(self, symbol: str, metrics: Dict):
        """Cache depth metrics."""
        self.depth_cache.set(f"depth_{symbol}", metrics)
    
    def get_volatility_metrics(self, symbol: str) -> Optional[Dict]:
        """Get cached volatility metrics."""
        return self.volatility_cache.get(f"volatility_{symbol}")
    
    def set_volatility_metrics(self, symbol: str, metrics: Dict):
        """Cache volatility metrics."""
        self.volatility_cache.set(f"volatility_{symbol}", metrics)
    
    def clear_all(self):
        """Clear all caches."""
        self.spread_cache.clear()
        self.depth_cache.clear()
        self.volatility_cache.clear()


# Global cache instances
_metrics_cache: Optional[MetricsCache] = None


def get_metrics_cache() -> MetricsCache:
    """Get or create metrics cache singleton."""
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = MetricsCache()
    return _metrics_cache
