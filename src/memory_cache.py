"""In-memory cache for pipeline results (fallback when Redis is unavailable)."""

from typing import Any, Dict, List, Optional

from .parquet_loader import extract_metrics_from_parquet


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

        If parquet_path is available, loads metrics from parquet file.
        Otherwise returns None to allow fallback to parquet loader.

        Returns:
            Cached metrics dictionary or None if not available.
        """
        if self._cache is None:
            return None
        
        # If we have a parquet_path, try to load metrics from it
        parquet_path = self._cache.get("parquet_path")
        if parquet_path:
            metrics = extract_metrics_from_parquet(parquet_path)
            if metrics is not None:
                return metrics
        
        # Otherwise return None to allow fallback to parquet loader
        return None

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
        explanation = self._cache.get("explanation")
        # Return None if explanation is empty string
        if explanation == "":
            return None
        return explanation

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

