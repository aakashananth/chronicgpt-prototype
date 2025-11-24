"""Pipeline module for processing health metrics."""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd

from .anomaly_detection import detect_anomalies
from .azure_storage_client import AzureStorageClient
from .config import config
from .llm_explainer import generate_explanation
from .redis_cache import RedisCacheClient
from .ultrahuman_client import UltrahumanClient


def run_daily_pipeline(days_back: int = 14) -> Dict[str, Any]:
    """Run the complete daily health metrics pipeline.

    This function orchestrates the entire flow:
    1. Fetches health metrics from UltraHuman API
    2. Converts to DataFrame and transforms data
    3. Detects anomalies using rolling baselines
    4. Generates LLM explanation for recent anomalies
    5. Saves enriched data to Parquet file

    Args:
        days_back: Number of days to look back from today (default: 14).

    Returns:
        Dictionary containing:
            - "enriched": DataFrame with all metrics and anomaly flags
            - "recent_anomalies": List of dicts for the last 5 anomalous days
            - "explanation": String explanation from LLM
            - "parquet_path": Path to saved Parquet file

    Raises:
        RuntimeError: If data fetching or processing fails.
        ValueError: If required data is missing.
    """
    # Step 1: Instantiate UltrahumanClient
    client = UltrahumanClient()

    # Step 2: Compute start and end dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Step 3: Call get_daily_metrics to get list of dicts
    raw_metrics = client.get_daily_metrics(start_date, end_date)

    if not raw_metrics:
        raise ValueError(
            f"No metrics data retrieved for date range {start_date.date()} to {end_date.date()}"
        )

    # Step 4: Transform raw metrics into DataFrame
    # The raw_metrics is a list of metric objects from the API
    # We need to group by date and extract the relevant fields
    daily_data = _transform_metrics_to_dataframe(raw_metrics)

    # Step 5: Rename columns (some may already be correct, but ensure consistency)
    # The columns should be: date, hrv, resting_hr, sleep_score, steps
    column_mapping = {
        "date": "date",
        "hrv_score": "hrv",
        "hrv": "hrv",  # In case it's already named hrv
        "resting_hr": "resting_hr",
        "sleep_score": "sleep_score",
        "steps": "steps",
    }

    # Only rename columns that exist and need renaming
    for old_name, new_name in column_mapping.items():
        if old_name in daily_data.columns and old_name != new_name:
            daily_data = daily_data.rename(columns={old_name: new_name})

    # Ensure we have the required columns
    required_columns = ["date", "hrv", "resting_hr", "sleep_score", "steps"]
    missing_columns = [col for col in required_columns if col not in daily_data.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns after transformation: {missing_columns}. "
            f"Available columns: {list(daily_data.columns)}"
        )

    # Step 6: Call detect_anomalies to get enriched DataFrame
    enriched_df = detect_anomalies(daily_data)

    # Step 7: Get last 5 anomalous rows (is_anomalous == True)
    anomalous_df = enriched_df[enriched_df["is_anomalous"] == True].tail(5)

    # Step 8: Convert to list of dicts
    # Convert date back to string for JSON serialization
    recent_anomalies = anomalous_df.copy()
    recent_anomalies["date"] = recent_anomalies["date"].astype(str)
    recent_anomalies_list = recent_anomalies.to_dict("records")

    # Step 9: Call generate_explanation
    explanation = generate_explanation(recent_anomalies_list)

    # Step 10: Save enriched DataFrame as Parquet file locally
    data_dir = config.storage.data_dir
    os.makedirs(data_dir, exist_ok=True)
    parquet_path = os.path.join(data_dir, "daily_metrics_enriched.parquet")
    enriched_df.to_parquet(parquet_path, index=False)

    # Step 11: Upload to Azure Blob Storage
    blob_path = None
    try:
        storage_client = AzureStorageClient()
        blob_path = storage_client.upload_parquet_file(parquet_path)
    except (ValueError, RuntimeError) as e:
        # Log error but don't fail the pipeline if Azure Storage is not configured
        # or if upload fails (allows local-only operation)
        print(f"Warning: Azure Blob Storage upload skipped: {e}", file=sys.stderr)

    # Step 12: Cache results in Redis
    result = {
        "enriched": enriched_df,
        "recent_anomalies": recent_anomalies_list,
        "explanation": explanation,
        "parquet_path": parquet_path,
        "blob_path": blob_path,
    }

    try:
        cache_client = RedisCacheClient()
        cache_client.cache_pipeline_result(result)
    except Exception as e:
        # Log error but don't fail the pipeline if Redis is not configured
        print(f"Warning: Redis caching skipped: {e}", file=sys.stderr)

    return result


def _transform_metrics_to_dataframe(raw_metrics: List[Dict[str, Any]]) -> pd.DataFrame:
    """Transform raw API metrics into a DataFrame with one row per date.

    The raw_metrics list contains metric objects from the API response.
    Each API call returns metric_data for a single date, so we need to:
    1. Group metrics by date
    2. Extract relevant fields (hrv, resting_hr, sleep_score, steps)
    3. Create one row per date

    Args:
        raw_metrics: List of metric dictionaries from the API.

    Returns:
        DataFrame with columns: date, hrv, resting_hr, sleep_score, steps
        (and optionally other metrics if available).
    """
    # Group metrics by date
    # The structure is: each item in raw_metrics is a metric object with type and object
    # We need to find the date from the day_start_timestamp in the objects

    date_metrics = {}

    for metric in raw_metrics:
        metric_type = metric.get("type")
        metric_obj = metric.get("object", {})

        # Extract date from day_start_timestamp (present in most metrics)
        day_start_ts = metric_obj.get("day_start_timestamp")
        if day_start_ts:
            date_key = datetime.fromtimestamp(day_start_ts).date()
        else:
            # Try to get date from Sleep object's bedtime_start
            if metric_type == "Sleep":
                bedtime_start = metric_obj.get("bedtime_start")
                if bedtime_start:
                    date_key = datetime.fromtimestamp(bedtime_start).date()
                else:
                    continue
            else:
                continue

        # Initialize date entry if not exists
        if date_key not in date_metrics:
            date_metrics[date_key] = {"date": date_key}

        # Extract relevant metrics based on type
        if metric_type == "avg_sleep_hrv":
            date_metrics[date_key]["hrv"] = metric_obj.get("value")
        elif metric_type == "sleep_rhr":
            date_metrics[date_key]["resting_hr"] = metric_obj.get("value")
        elif metric_type == "Sleep":
            sleep_score_obj = metric_obj.get("sleep_score", {})
            if isinstance(sleep_score_obj, dict):
                date_metrics[date_key]["sleep_score"] = sleep_score_obj.get("score")
            else:
                date_metrics[date_key]["sleep_score"] = sleep_score_obj
        elif metric_type == "steps":
            # Steps can be a single value or values array
            if "total" in metric_obj:
                date_metrics[date_key]["steps"] = metric_obj.get("total")
            elif "values" in metric_obj and metric_obj["values"]:
                # Sum up all step values for the day
                step_values = [
                    v.get("value", 0) for v in metric_obj["values"] if isinstance(v, dict)
                ]
                date_metrics[date_key]["steps"] = sum(step_values) if step_values else 0
        elif metric_type == "recovery_index":
            date_metrics[date_key]["recovery_index"] = metric_obj.get("value")
        elif metric_type == "movement_index":
            date_metrics[date_key]["movement_index"] = metric_obj.get("value")
        elif metric_type == "vo2_max":
            date_metrics[date_key]["vo2_max"] = metric_obj.get("value")
        elif metric_type == "active_minutes":
            date_metrics[date_key]["active_minutes"] = metric_obj.get("value")

    # Convert to DataFrame
    if not date_metrics:
        raise ValueError("No valid date metrics found in raw_metrics")

    df = pd.DataFrame(list(date_metrics.values()))

    # Ensure date column is present and properly typed
    if "date" not in df.columns:
        raise ValueError("Date column missing after transformation")

    return df
