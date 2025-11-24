"""In-memory cache for pipeline results (fallback when Redis is unavailable)."""

from typing import Any, Dict, List, Optional


class MemoryCache:
    """Simple in-memory cache for storing pipeline results."""

    def __init__(self):
        """Initialize the memory cache."""
        self._cache: Optional[Dict[str, Any]] = None

    def store_pipeline_result(self, result: Dict[str, Any]) -> None:
        """Store pipeline result in memory.

        Args:
            result: Pipeline result dictionary.
        """
        # Store a copy without the DataFrame (not JSON serializable)
        self._cache = {
            "recent_anomalies": result.get("recent_anomalies", []),
            "explanation": result.get("explanation", ""),
            "parquet_path": result.get("parquet_path", ""),
            "blob_path": result.get("blob_path"),
        }

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached metrics from memory.

        Returns:
            Cached metrics dictionary or None if not available.
        """
        if self._cache is None:
            return None
        # Return a metrics-like structure (could be enriched from parquet if needed)
        return self._cache

    def get_anomalies(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached anomalies from memory.

        Returns:
            List of anomalies or None if not available.
        """
        if self._cache is None:
            return None
        return self._cache.get("recent_anomalies")

    def get_explanation(self) -> Optional[str]:
        """Get cached explanation from memory.

        Returns:
            Explanation string or None if not available.
        """
        if self._cache is None:
            return None
        return self._cache.get("explanation")

    def get_blob_path(self) -> Optional[str]:
        """Get cached blob path from memory.

        Returns:
            Blob path string or None if not available.
        """
        if self._cache is None:
            return None
        return self._cache.get("blob_path")

    def get_parquet_path(self) -> Optional[str]:
        """Get cached parquet path from memory.

        Returns:
            Parquet path string or None if not available.
        """
        if self._cache is None:
            return None
        return self._cache.get("parquet_path")

    def clear(self) -> None:
        """Clear the cache."""
        self._cache = None


# Global instance
memory_cache = MemoryCache()

