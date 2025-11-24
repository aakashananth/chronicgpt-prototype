"""FastAPI application for health metrics pipeline."""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .memory_cache import memory_cache
from .parquet_loader import (
    extract_anomalies_from_parquet,
    extract_metrics_from_parquet,
    get_parquet_path,
)
from .pipeline import run_daily_pipeline
from .redis_cache import RedisCacheClient

app = FastAPI(
    title="Health Metrics LLM Prototype API",
    description="API for health metrics analysis and anomaly detection",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    Fallback order:
    1. Try Redis (if configured and reachable)
    2. Try in-memory cache
    3. Try loading from parquet file
    4. Return 404 if all fail

    Returns:
        Cached metrics dictionary.
    """
    # Step 1: Try Redis
    cached_metrics = cache_client.get_cached_metrics()
    if cached_metrics is not None:
        return cached_metrics

    # Step 2: Try in-memory cache
    cached_metrics = memory_cache.get_metrics()
    if cached_metrics is not None:
        return cached_metrics

    # Step 3: Try loading from parquet
    parquet_path = get_parquet_path()
    if parquet_path:
        cached_metrics = extract_metrics_from_parquet(parquet_path)
        if cached_metrics is not None:
            return cached_metrics

    # Step 4: Return 404
    raise HTTPException(
        status_code=404,
        detail="No cached metrics found. Run the pipeline first via POST /pipeline/run",
    )


@app.get("/pipeline/anomalies")
async def get_anomalies() -> List[Dict[str, Any]]:
    """Get cached anomalies list.

    Fallback order:
    1. Try Redis (if configured and reachable)
    2. Try in-memory cache
    3. Try loading from parquet file
    4. Return 404 if all fail

    Returns:
        List of cached anomalies.
    """
    # Step 1: Try Redis
    cached_anomalies = cache_client.get_cached_anomalies()
    if cached_anomalies is not None:
        return cached_anomalies

    # Step 2: Try in-memory cache
    cached_anomalies = memory_cache.get_anomalies()
    if cached_anomalies is not None:
        return cached_anomalies

    # Step 3: Try loading from parquet
    parquet_path = get_parquet_path()
    if parquet_path:
        cached_anomalies = extract_anomalies_from_parquet(parquet_path)
        if cached_anomalies is not None:
            return cached_anomalies

    # Step 4: Return 404
    raise HTTPException(
        status_code=404,
        detail="No cached anomalies found. Run the pipeline first via POST /pipeline/run",
    )


@app.get("/pipeline/explanation")
async def get_explanation() -> Dict[str, str]:
    """Get cached LLM explanation.

    Fallback order:
    1. Try Redis (if configured and reachable)
    2. Try in-memory cache
    3. Return 404 (explanation not stored in parquet)

    Returns:
        Dictionary containing the explanation text.
    """
    # Step 1: Try Redis
    cached_explanation = cache_client.get_cached_explanation()
    if cached_explanation is not None:
        return {"explanation": cached_explanation}

    # Step 2: Try in-memory cache
    cached_explanation = memory_cache.get_explanation()
    if cached_explanation is not None:
        return {"explanation": cached_explanation}

    # Step 3: Return 404 (explanation not stored in parquet)
    raise HTTPException(
        status_code=404,
        detail="No cached explanation found. Run the pipeline first via POST /pipeline/run",
    )


@app.get("/pipeline/blob-path")
async def get_blob_path() -> Dict[str, str]:
    """Get cached Azure Blob Storage path.

    Fallback order:
    1. Try Redis (if configured and reachable)
    2. Try in-memory cache
    3. Return 404 (blob path not stored in parquet)

    Returns:
        Dictionary containing the blob path.
    """
    # Step 1: Try Redis
    cached_blob_path = cache_client.get_cached_blob_path()
    if cached_blob_path is not None:
        return {"blob_path": cached_blob_path}

    # Step 2: Try in-memory cache
    cached_blob_path = memory_cache.get_blob_path()
    if cached_blob_path is not None:
        return {"blob_path": cached_blob_path}

    # Step 3: Return 404 (blob path not stored in parquet)
    raise HTTPException(
        status_code=404,
        detail="No cached blob path found. Run the pipeline first via POST /pipeline/run",
    )

