"""FastAPI application for health metrics pipeline."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .azure_storage_client import AzureStorageClient
from .config import config
from .memory_cache import memory_cache
from .parquet_loader import (
    extract_anomalies_from_parquet,
    extract_metrics_from_parquet,
    get_parquet_path,
)
from .pipeline import run_daily_pipeline, run_incremental_pipeline
from .redis_cache import RedisCacheClient

app = FastAPI(
    title="Health Metrics LLM Prototype API",
    description="API for health metrics analysis and anomaly detection",
    version="1.0.0",
)

# Configure CORS - Allow all Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://chronicgpt-ui.vercel.app",
        "https://chronicgpt-ui-aakashananths-projects.vercel.app",
        "https://chronicgpt-prototype.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
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
            "/pipeline/run_incremental": "Run the incremental pipeline (only new dates)",
            "/pipeline/metrics": "Get cached metrics",
            "/pipeline/metrics/history": "Get historical metrics for charts",
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
            },
        }

    if redis_client is None:
        return {
            "status": "connection_failed",
            "message": "Redis connection failed. Check your credentials and network.",
            "config": {
                "host": cache_client.host,
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            },
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
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Redis connection error: {str(e)}",
            "config": {
                "host": cache_client.host,
                "port": cache_client.port,
                "ssl": cache_client.ssl,
            },
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
        raise HTTPException(
            status_code=500, detail=f"Pipeline execution failed: {str(e)}"
        )


@app.post("/pipeline/run_incremental")
async def run_incremental_pipeline_endpoint(days_back: int = 14) -> Dict[str, Any]:
    """Run the incremental pipeline for the configured patient_id.

    Only new dates within the last `days_back` days will be fetched and processed.

    Args:
        days_back: Number of days to look back from today (default: 14).

    Returns:
        Pipeline results including new dates processed, anomalies, explanation, and paths.
    """
    try:
        # Run incremental pipeline
        result = run_incremental_pipeline(days_back=days_back)

        # Cache the result (already done in run_incremental_pipeline, but ensure it's cached)
        cache_client.cache_pipeline_result(result)

        # Prepare response (exclude DataFrame for JSON serialization)
        response = {
            "status": "success",
            "new_dates_processed": result.get("new_dates_processed", []),
            "anomaly_count": result.get("anomaly_count", 0),
            "recent_anomalies": result.get("recent_anomalies", []),
            "explanation": result.get("explanation", ""),
            "blob_path": result.get("blob_path"),
            "curated_blob_paths": result.get("curated_blob_paths", []),
            "metrics_count": len(result.get("enriched", [])),
        }

        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Incremental pipeline execution failed: {str(e)}"
        )


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


@app.get("/pipeline/metrics/history")
async def get_metrics_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    end_date: Optional[str] = Query(
        None, description="End date in YYYY-MM-DD format (defaults to today)"
    ),
) -> Dict[str, Any]:
    """Get historical metrics data in chart-friendly format.

    Loads curated daily metrics from Azure Blob Storage for the configured patient_id
    within the specified date range. Returns data as arrays suitable for charting.

    Args:
        days: Number of days to look back from end_date (default: 30, max: 365).
        end_date: End date in YYYY-MM-DD format. If not provided, uses today.

    Returns:
        Dictionary with chart-friendly data:
        {
            "dates": ["YYYY-MM-DD", ...],
            "hrv": [number, ...],
            "resting_hr": [number, ...],
            "sleep_score": [number, ...],
            "steps": [number, ...],
            "recovery_index": [number | null, ...],
            "movement_index": [number | null, ...],
            "active_minutes": [number | null, ...],
            "vo2_max": [number | null, ...],
            "low_hrv_flag": [bool, ...],
            "high_rhr_flag": [bool, ...],
            "low_sleep_flag": [bool, ...],
            "low_steps_flag": [bool, ...],
            "is_anomalous": [bool, ...],
            "anomaly_severity": [number, ...],
            "date_range": {
                "start": "YYYY-MM-DD",
                "end": "YYYY-MM-DD"
            },
            "total_records": number
        }

    Raises:
        HTTPException: If patient_id is not configured or data loading fails.
    """
    # Get patient_id from config
    patient_id = config.ultrahuman.patient_id
    if not patient_id:
        raise HTTPException(
            status_code=400,
            detail="patient_id is not configured. Set ULTRAHUMAN_PATIENT_ID or ULTRAHUMAN_EMAIL in .env",
        )

    # Parse end_date or use today
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {end_date}. Use YYYY-MM-DD format.",
            )
    else:
        end_date_obj = datetime.now().date()

    # Calculate start_date
    start_date_obj = end_date_obj - timedelta(days=days - 1)

    try:
        # Load data from Azure Blob Storage
        storage_client = AzureStorageClient()
        df = storage_client.load_curated_metrics_for_date_range(
            patient_id, start_date_obj, end_date_obj
        )

        # Create a complete date range from start_date to end_date (inclusive)
        try:
            date_range = pd.date_range(
                start=start_date_obj, end=end_date_obj, freq="D"
            ).date.tolist()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date range: {start_date_obj} to {end_date_obj}. Error: {str(e)}",
            )

        if df.empty:
            # Return empty arrays for all dates in range
            return {
                "dates": [d.strftime("%Y-%m-%d") for d in date_range],
                "hrv": [],
                "resting_hr": [],
                "sleep_score": [],
                "steps": [],
                "recovery_index": [],
                "movement_index": [],
                "active_minutes": [],
                "vo2_max": [],
                "low_hrv_flag": [],
                "high_rhr_flag": [],
                "low_sleep_flag": [],
                "low_steps_flag": [],
                "is_anomalous": [],
                "anomaly_severity": [],
                "date_range": {
                    "start": start_date_obj.strftime("%Y-%m-%d"),
                    "end": end_date_obj.strftime("%Y-%m-%d"),
                },
                "total_records": 0,
            }

        # Ensure date column exists and is sorted
        if "date" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail="DataFrame missing 'date' column after loading from storage",
            )

        # Convert date column to datetime if needed, then to date
        if df["date"].dtype == "object":
            df["date"] = pd.to_datetime(df["date"]).dt.date
        elif hasattr(df["date"].dtype, "tz"):
            # Handle timezone-aware datetime
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        # Set date as index for alignment
        try:
            df_indexed = df.set_index("date")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set date as index: {str(e)}",
            )

        # Reindex to complete date range with forward fill for missing days
        # This ensures we always return a valid time-series with no gaps
        # Reindex first, then forward fill missing values (carry last known value forward)
        # Explicitly specify fill_value=None for reindex, then use ffill() for forward fill
        try:
            df_aligned = df_indexed.reindex(date_range, fill_value=None)
            # Forward fill missing values - use ffill() instead of deprecated fillna(method="ffill")
            df_aligned = df_aligned.ffill()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reindex DataFrame: {str(e)}",
            )

        # Reset index to get date back as a column
        df_aligned = df_aligned.reset_index()
        df_aligned.rename(columns={"index": "date"}, inplace=True)

        # Convert dates to strings for JSON serialization
        dates = [d.strftime("%Y-%m-%d") for d in df_aligned["date"].tolist()]

        # Extract metric arrays with proper null handling
        def get_array(column_name: str, default_value=None):
            """Get array from DataFrame column, using default_value for nulls."""
            if column_name in df_aligned.columns:
                return df_aligned[column_name].fillna(default_value).tolist()
            return [default_value] * len(dates) if default_value is not None else []

        # Build response
        response = {
            "dates": dates,
            "hrv": get_array("hrv"),
            "resting_hr": get_array("resting_hr"),
            "sleep_score": get_array("sleep_score"),
            "steps": get_array("steps"),
            "recovery_index": get_array("recovery_index", None),
            "movement_index": get_array("movement_index", None),
            "active_minutes": get_array("active_minutes", None),
            "vo2_max": get_array("vo2_max", None),
            "low_hrv_flag": get_array("low_hrv_flag", False),
            "high_rhr_flag": get_array("high_rhr_flag", False),
            "low_sleep_flag": get_array("low_sleep_flag", False),
            "low_steps_flag": get_array("low_steps_flag", False),
            "is_anomalous": get_array("is_anomalous", False),
            "anomaly_severity": get_array("anomaly_severity", 0),
            "date_range": {
                "start": start_date_obj.strftime("%Y-%m-%d"),
                "end": end_date_obj.strftime("%Y-%m-%d"),
            },
            "total_records": len(df),
        }

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load metrics history: {str(e)}",
        )
