"""
Overpass API proxy service with caching and rate limiting
"""
import os
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import lru_cache
import httpx
try:
    from app.config import get_overpass_config
except ImportError:
    # Fallback if config not available
    def get_overpass_config():
        import os
        base_url = os.getenv("OVERPASS_API_URL", "https://overpass-api.de")
        # Remove /api/interpreter if present (for backward compatibility)
        if base_url.endswith("/api/interpreter"):
            base_url = base_url[:-15]
        return {
            "url": base_url.rstrip("/"),
            "cache_ttl": int(os.getenv("OVERPASS_CACHE_TTL", "300")),
            "rate_limit": int(os.getenv("OVERPASS_RATE_LIMIT", "60")),
            "timeout": int(os.getenv("OVERPASS_TIMEOUT", "60"))
        }

logger = logging.getLogger(__name__)


class OverpassProxyService:
    """Service for proxying Overpass API queries with caching and rate limiting"""
    
    def __init__(self):
        self.config = get_overpass_config()
        # Ensure URL doesn't have trailing slash
        base_url = self.config["url"].rstrip("/")
        # Remove /api/interpreter if present (for backward compatibility)
        if base_url.endswith("/api/interpreter"):
            base_url = base_url[:-15]  # Remove "/api/interpreter"
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config["timeout"], connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._rate_limit_tracker: Dict[str, List[datetime]] = {}
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query string"""
        return hashlib.sha256(query.encode()).hexdigest()
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = datetime.now()
        if client_id not in self._rate_limit_tracker:
            self._rate_limit_tracker[client_id] = []
        
        # Remove old entries (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self._rate_limit_tracker[client_id] = [
            ts for ts in self._rate_limit_tracker[client_id] if ts > cutoff
        ]
        
        # Check if limit exceeded
        if len(self._rate_limit_tracker[client_id]) >= self.config["rate_limit"]:
            return True
        
        # Add current request
        self._rate_limit_tracker[client_id].append(now)
        return False
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if cache_key not in self._cache:
            return None
        
        cached = self._cache[cache_key]
        age = datetime.now() - cached["timestamp"]
        
        if age.total_seconds() > self.config["cache_ttl"]:
            # Cache expired, remove it
            del self._cache[cache_key]
            return None
        
        return cached["data"]
    
    def _set_cached_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store response in cache"""
        self._cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    async def execute_query(
        self,
        query: str,
        client_id: str = "default",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Overpass QL query with caching and rate limiting
        
        Args:
            query: Overpass QL query string
            client_id: Client identifier for rate limiting
            use_cache: Whether to use cache for this query
        
        Returns:
            Overpass API response as dictionary
        
        Raises:
            httpx.HTTPError: If request fails
            ValueError: If rate limited
        """
        # Check rate limit
        if self._is_rate_limited(client_id):
            raise ValueError(
                f"Rate limit exceeded. Maximum {self.config['rate_limit']} queries per minute."
            )
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(query)
            cached = self._get_cached_response(cache_key)
            if cached is not None:
                logger.info(f"Cache hit for query: {cache_key[:16]}...")
                return cached
        
        # Execute query
        try:
            logger.info(f"Executing Overpass query (client: {client_id})")
            response = await self.client.post(
                f"{self.base_url}/api/interpreter",
                content=query,
                headers={"Content-Type": "text/plain"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Cache successful responses
            if use_cache:
                cache_key = self._get_cache_key(query)
                self._set_cached_response(cache_key, data)
            
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Overpass API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Overpass API request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing Overpass query: {e}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check Overpass API health status"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/status",
                timeout=5.0
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "available": True,
                "version": response.headers.get("X-Overpass-Version"),
                "message": "Overpass API is available"
            }
        except Exception as e:
            logger.warning(f"Overpass API health check failed: {e}")
            return {
                "status": "unhealthy",
                "available": False,
                "message": str(e)
            }
    
    async def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached responses")
        return count
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global service instance
_overpass_service: Optional[OverpassProxyService] = None


def get_overpass_service() -> OverpassProxyService:
    """Get or create global Overpass proxy service instance"""
    global _overpass_service
    if _overpass_service is None:
        _overpass_service = OverpassProxyService()
    return _overpass_service


async def close_overpass_service():
    """Close global Overpass proxy service"""
    global _overpass_service
    if _overpass_service is not None:
        await _overpass_service.close()
        _overpass_service = None

