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
    import redis
    from redis.exceptions import RedisError, TimeoutError
    
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
        # Try to get more detailed error by attempting connection directly
        error_details = None
        try:
            test_client = redis.Redis(
                host=cache_client.host,
                port=cache_client.port,
                password=cache_client.password,
                ssl=cache_client.ssl,
                ssl_cert_reqs=None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            test_client.ping()
        except TimeoutError as e:
            error_details = f"Timeout: {str(e)} - Firewall or network issue"
        except redis.ConnectionError as e:
            error_details = f"Connection Error: {str(e)}"
        except redis.AuthenticationError as e:
            error_details = f"Authentication Error: {str(e)} - Check REDIS_ACCESS_KEY"
        except Exception as e:
            error_details = f"{type(e).__name__}: {str(e)}"
        
        return {
            "status": "connection_failed",
            "message": "Redis connection failed. Check your credentials and network.",
            "error_details": error_details,
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
            "error_type": type(e).__name__,
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
        date_range = []
        current_date = start_date_obj
        while current_date <= end_date_obj:
            date_range.append(current_date)
            current_date += timedelta(days=1)

        # Build a dictionary mapping date -> row data for fast lookup
        date_to_data = {}
        if not df.empty and "date" in df.columns:
            # Convert date column to date type if needed
            if df["date"].dtype == "object":
                df["date"] = pd.to_datetime(df["date"]).dt.date
            elif hasattr(df["date"].dtype, "tz"):
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date
            
            # Convert DataFrame rows to dictionary by date
            for _, row in df.iterrows():
                row_date = row["date"]
                if isinstance(row_date, str):
                    row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                date_to_data[row_date] = row.to_dict()

        # Build arrays by iterating through date range with forward fill
        dates = []
        hrv_values = []
        resting_hr_values = []
        sleep_score_values = []
        steps_values = []
        recovery_index_values = []
        movement_index_values = []
        active_minutes_values = []
        vo2_max_values = []
        low_hrv_flag_values = []
        high_rhr_flag_values = []
        low_sleep_flag_values = []
        low_steps_flag_values = []
        is_anomalous_values = []
        anomaly_severity_values = []

        # Track last known values for forward fill
        last_values = {
            "hrv": None,
            "resting_hr": None,
            "sleep_score": None,
            "steps": None,
            "recovery_index": None,
            "movement_index": None,
            "active_minutes": None,
            "vo2_max": None,
            "low_hrv_flag": False,
            "high_rhr_flag": False,
            "low_sleep_flag": False,
            "low_steps_flag": False,
            "is_anomalous": False,
            "anomaly_severity": 0,
        }

        for date_obj in date_range:
            dates.append(date_obj.strftime("%Y-%m-%d"))
            
            # Get data for this date, or use forward-filled values
            if date_obj in date_to_data:
                row = date_to_data[date_obj]
                # Update last known values
                last_values["hrv"] = row.get("hrv")
                last_values["resting_hr"] = row.get("resting_hr")
                last_values["sleep_score"] = row.get("sleep_score")
                last_values["steps"] = row.get("steps")
                last_values["recovery_index"] = row.get("recovery_index")
                last_values["movement_index"] = row.get("movement_index")
                last_values["active_minutes"] = row.get("active_minutes")
                last_values["vo2_max"] = row.get("vo2_max")
                last_values["low_hrv_flag"] = bool(row.get("low_hrv_flag", False))
                last_values["high_rhr_flag"] = bool(row.get("high_rhr_flag", False))
                last_values["low_sleep_flag"] = bool(row.get("low_sleep_flag", False))
                last_values["low_steps_flag"] = bool(row.get("low_steps_flag", False))
                last_values["is_anomalous"] = bool(row.get("is_anomalous", False))
                last_values["anomaly_severity"] = int(row.get("anomaly_severity", 0))
            
            # Append values (use forward-filled if no data for this date)
            hrv_values.append(last_values["hrv"])
            resting_hr_values.append(last_values["resting_hr"])
            sleep_score_values.append(last_values["sleep_score"])
            steps_values.append(last_values["steps"])
            recovery_index_values.append(last_values["recovery_index"])
            movement_index_values.append(last_values["movement_index"])
            active_minutes_values.append(last_values["active_minutes"])
            vo2_max_values.append(last_values["vo2_max"])
            low_hrv_flag_values.append(last_values["low_hrv_flag"])
            high_rhr_flag_values.append(last_values["high_rhr_flag"])
            low_sleep_flag_values.append(last_values["low_sleep_flag"])
            low_steps_flag_values.append(last_values["low_steps_flag"])
            is_anomalous_values.append(last_values["is_anomalous"])
            anomaly_severity_values.append(last_values["anomaly_severity"])

        # Build response
        response = {
            "dates": dates,
            "hrv": hrv_values,
            "resting_hr": resting_hr_values,
            "sleep_score": sleep_score_values,
            "steps": steps_values,
            "recovery_index": recovery_index_values,
            "movement_index": movement_index_values,
            "active_minutes": active_minutes_values,
            "vo2_max": vo2_max_values,
            "low_hrv_flag": low_hrv_flag_values,
            "high_rhr_flag": high_rhr_flag_values,
            "low_sleep_flag": low_sleep_flag_values,
            "low_steps_flag": low_steps_flag_values,
            "is_anomalous": is_anomalous_values,
            "anomaly_severity": anomaly_severity_values,
            "date_range": {
                "start": start_date_obj.strftime("%Y-%m-%d"),
                "end": end_date_obj.strftime("%Y-%m-%d"),
            },
            "total_records": len(date_to_data),  # Count of actual data points, not date range length
        }

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load metrics history: {str(e)}",
        )
