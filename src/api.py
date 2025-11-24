"""FastAPI application for health metrics pipeline."""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from .pipeline import run_daily_pipeline
from .redis_cache import RedisCacheClient

app = FastAPI(
    title="Health Metrics LLM Prototype API",
    description="API for health metrics analysis and anomaly detection",
    version="1.0.0",
)

# Initialize Redis cache client
cache_client = RedisCacheClient()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Health Metrics LLM Prototype API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/health/redis": "Check Redis connection status",
            "/pipeline/run": "Run the daily pipeline",
            "/pipeline/metrics": "Get cached metrics",
            "/pipeline/anomalies": "Get cached anomalies",
            "/pipeline/explanation": "Get cached explanation",
            "/pipeline/blob-path": "Get cached blob path",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/health/redis")
async def redis_health_check():
    """Check Redis connection status."""
    redis_client = cache_client._get_redis_client()
    
    if not cache_client.host or not cache_client.password:
        return {
            "status": "not_configured",
            "message": "Redis is not configured. Set REDIS_HOST and REDIS_ACCESS_KEY in .env",
            "config": {
                "host": cache_client.host or "not set",
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            }
        }
    
    if redis_client is None:
        return {
            "status": "connection_failed",
            "message": "Redis connection failed. Check your credentials and network.",
            "config": {
                "host": cache_client.host,
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            }
        }
    
    try:
        # Test connection
        redis_client.ping()
        return {
            "status": "connected",
            "message": "Redis is connected and working",
            "config": {
                "host": cache_client.host,
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Redis connection error: {str(e)}",
            "config": {
                "host": cache_client.host,
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            }
        }


@app.post("/pipeline/run")
async def run_pipeline(days_back: int = 14) -> Dict[str, Any]:
    """Run the daily health metrics pipeline.

    Args:
        days_back: Number of days to look back from today (default: 14).

    Returns:
        Pipeline results including enriched data, anomalies, explanation, and paths.
    """
    try:
        # Run pipeline
        result = run_daily_pipeline(days_back=days_back)

        # Cache the result
        cache_client.cache_pipeline_result(result)

        # Prepare response (exclude DataFrame for JSON serialization)
        response = {
            "status": "success",
            "recent_anomalies": result.get("recent_anomalies", []),
            "explanation": result.get("explanation", ""),
            "parquet_path": result.get("parquet_path", ""),
            "blob_path": result.get("blob_path"),
            "metrics_count": len(result.get("enriched", [])),
        }

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@app.get("/pipeline/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get cached metrics data.

    Returns:
        Cached metrics dictionary.
    """
    cached_metrics = cache_client.get_cached_metrics()
    if cached_metrics is None:
        # Check if Redis is configured
        if not cache_client.host or not cache_client.password:
            raise HTTPException(
                status_code=503,
                detail="Redis cache is not configured. Set REDIS_HOST and REDIS_ACCESS_KEY in .env file. "
                "Alternatively, run the pipeline via POST /pipeline/run to get fresh data.",
            )
        # Redis is configured but no cached data found
        raise HTTPException(
            status_code=404,
            detail="No cached metrics found. Run the pipeline first via POST /pipeline/run",
        )
    return cached_metrics


@app.get("/pipeline/anomalies")
async def get_anomalies() -> List[Dict[str, Any]]:
    """Get cached anomalies list.

    Returns:
        List of cached anomalies.
    """
    cached_anomalies = cache_client.get_cached_anomalies()
    if cached_anomalies is None:
        if not cache_client.host or not cache_client.password:
            raise HTTPException(
                status_code=503,
                detail="Redis cache is not configured. Set REDIS_HOST and REDIS_ACCESS_KEY in .env file. "
                "Alternatively, run the pipeline via POST /pipeline/run to get fresh data.",
            )
        raise HTTPException(
            status_code=404,
            detail="No cached anomalies found. Run the pipeline first via POST /pipeline/run",
        )
    return cached_anomalies


@app.get("/pipeline/explanation")
async def get_explanation() -> Dict[str, str]:
    """Get cached LLM explanation.

    Returns:
        Dictionary containing the explanation text.
    """
    cached_explanation = cache_client.get_cached_explanation()
    if cached_explanation is None:
        if not cache_client.host or not cache_client.password:
            raise HTTPException(
                status_code=503,
                detail="Redis cache is not configured. Set REDIS_HOST and REDIS_ACCESS_KEY in .env file. "
                "Alternatively, run the pipeline via POST /pipeline/run to get fresh data.",
            )
        raise HTTPException(
            status_code=404,
            detail="No cached explanation found. Run the pipeline first via POST /pipeline/run",
        )
    return {"explanation": cached_explanation}


@app.get("/pipeline/blob-path")
async def get_blob_path() -> Dict[str, str]:
    """Get cached Azure Blob Storage path.

    Returns:
        Dictionary containing the blob path.
    """
    cached_blob_path = cache_client.get_cached_blob_path()
    if cached_blob_path is None:
        if not cache_client.host or not cache_client.password:
            raise HTTPException(
                status_code=503,
                detail="Redis cache is not configured. Set REDIS_HOST and REDIS_ACCESS_KEY in .env file. "
                "Alternatively, run the pipeline via POST /pipeline/run to get fresh data.",
            )
        raise HTTPException(
            status_code=404,
            detail="No cached blob path found. Run the pipeline first via POST /pipeline/run",
        )
    return {"blob_path": cached_blob_path}

