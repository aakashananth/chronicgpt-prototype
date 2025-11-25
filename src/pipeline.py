"""Pipeline module for processing health metrics."""

import os
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from .anomaly_detection import detect_anomalies
from .azure_storage_client import AzureStorageClient
from .config import config
from .llm_explainer import generate_explanation
from .memory_cache import memory_cache
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

    # Step 4.5: Add patient_id column to the DataFrame
    patient_id = config.ultrahuman.patient_id
    daily_data["patient_id"] = patient_id

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

    # Step 10: Save enriched DataFrame as Parquet file locally (for debugging)
    data_dir = config.storage.data_dir
    os.makedirs(data_dir, exist_ok=True)
    parquet_path = os.path.join(data_dir, "daily_metrics_enriched.parquet")
    enriched_df.to_parquet(parquet_path, index=False)

    # Step 11: Upload curated metrics to Azure Blob Storage (partitioned by patient_id and date)
    uploaded_blobs = []
    skipped_dates = []
    try:
        storage_client = AzureStorageClient()
        # Loop over each row and upload individually
        for _, row in enriched_df.iterrows():
            patient_id = row.get("patient_id")
            date_obj = row.get("date")
            
            # Ensure date is a date object (not datetime or string)
            if isinstance(date_obj, str):
                from datetime import datetime as dt
                date_obj = dt.strptime(date_obj, "%Y-%m-%d").date()
            elif isinstance(date_obj, date):
                # Already a date object
                pass
            elif hasattr(date_obj, "date") and callable(getattr(date_obj, "date", None)):
                # datetime object - convert to date
                date_obj = date_obj.date()
            else:
                # Try to convert using pandas
                date_obj = pd.to_datetime(date_obj).date()
            
            # Convert row to single-row DataFrame
            row_df = pd.DataFrame([row])
            
            try:
                blob_path = storage_client.upload_curated_daily_metrics(
                    patient_id, date_obj, row_df
                )
                if blob_path:
                    uploaded_blobs.append(blob_path)
            except Exception as e:
                # If blob already exists, it's skipped (handled in upload method)
                # Other errors are logged
                if "already exist" in str(e).lower() or "ResourceExistsError" in str(type(e).__name__):
                    skipped_dates.append((patient_id, date_obj))
                else:
                    print(
                        f"Warning: Failed to upload curated metrics for patient {patient_id}, "
                        f"date {date_obj}: {e}",
                        file=sys.stderr,
                    )
        
        # Log summary
        if uploaded_blobs:
            print(
                f"Info: Uploaded {len(uploaded_blobs)} curated metric files to Azure Blob Storage",
                file=sys.stderr,
            )
        if skipped_dates:
            print(
                f"Info: Skipped {len(skipped_dates)} dates (already exist in storage)",
                file=sys.stderr,
            )
        
        # For backward compatibility, use the first uploaded blob path or None
        blob_path = uploaded_blobs[0] if uploaded_blobs else None
        
    except (ValueError, RuntimeError) as e:
        # Log error but don't fail the pipeline if Azure Storage is not configured
        # or if upload fails (allows local-only operation)
        print(f"Warning: Azure Blob Storage upload skipped: {e}", file=sys.stderr)
        blob_path = None

    # Step 12: Cache results in Redis
    result = {
        "enriched": enriched_df,
        "recent_anomalies": recent_anomalies_list,
        "explanation": explanation,
        "parquet_path": parquet_path,
        "blob_path": blob_path,
    }

    # Cache results in Redis (if available)
    try:
        cache_client = RedisCacheClient()
        cache_client.cache_pipeline_result(result)
    except Exception as e:
        # Log error but don't fail the pipeline if Redis is not configured
        print(f"Warning: Redis caching skipped: {e}", file=sys.stderr)

    # Always store in memory cache as fallback
    memory_cache.store_pipeline_result(result)

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


def _process_single_date(
    client: UltrahumanClient,
    storage_client: AzureStorageClient,
    patient_id: str,
    target_date: date,
) -> Optional[pd.DataFrame]:
    """Process a single date: fetch, transform, detect anomalies, and upload.

    Args:
        client: UltrahumanClient instance.
        storage_client: AzureStorageClient instance.
        patient_id: Patient identifier.
        target_date: Date to process.

    Returns:
        Single-row enriched DataFrame if successful, None otherwise.
    """
    try:
        # Fetch raw metrics for this date
        target_datetime = datetime.combine(target_date, datetime.min.time())
        raw_metrics = client._fetch_for_date(target_datetime)

        if not raw_metrics:
            print(
                f"Warning: No metrics found for patient {patient_id}, date {target_date}",
                file=sys.stderr,
            )
            return None

        # Transform to DataFrame
        daily_data = _transform_metrics_to_dataframe(raw_metrics)

        # Add patient_id
        daily_data["patient_id"] = patient_id

        # Rename columns if needed
        column_mapping = {
            "hrv_score": "hrv",
            "hrv": "hrv",
        }
        for old_name, new_name in column_mapping.items():
            if old_name in daily_data.columns and old_name != new_name:
                daily_data = daily_data.rename(columns={old_name: new_name})

        # Ensure required columns exist
        required_columns = ["date", "hrv", "resting_hr", "sleep_score", "steps"]
        missing_columns = [
            col for col in required_columns if col not in daily_data.columns
        ]
        if missing_columns:
            print(
                f"Warning: Missing columns for date {target_date}: {missing_columns}",
                file=sys.stderr,
            )
            return None

        # For anomaly detection, we need a window. Load recent data if available.
        # For now, use a minimal window - just this date (anomaly detection will use min_periods=1)
        enriched_df = detect_anomalies(daily_data)

        # Upload curated metrics (raw metrics already uploaded by client._fetch_for_date)
        uploaded_blobs = []
        for _, row in enriched_df.iterrows():
            date_obj = row.get("date")
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            elif isinstance(date_obj, date):
                pass
            elif hasattr(date_obj, "date") and callable(getattr(date_obj, "date", None)):
                date_obj = date_obj.date()
            else:
                date_obj = pd.to_datetime(date_obj).date()

            row_df = pd.DataFrame([row])
            blob_path = storage_client.upload_curated_daily_metrics(
                patient_id, date_obj, row_df
            )
            if blob_path:
                uploaded_blobs.append(blob_path)

        if uploaded_blobs:
            print(
                f"Info: Processed and uploaded metrics for patient {patient_id}, date {target_date}",
                file=sys.stderr,
            )
            return enriched_df
        else:
            print(
                f"Info: Metrics for patient {patient_id}, date {target_date} already exist (skipped)",
                file=sys.stderr,
            )
            return None

    except Exception as e:
        print(
            f"Error processing date {target_date} for patient {patient_id}: {e}",
            file=sys.stderr,
        )
        return None


def run_incremental_pipeline(days_back: int = 14) -> Dict[str, Any]:
    """Incremental ingestion and processing for the configured patient_id.

    Only processes new dates within the last `days_back` days that don't already
    exist in Azure Blob Storage.

    Steps:
      1. Get patient_id from config.ultrahuman.patient_id.
      2. Ask the storage client for existing curated dates via list_curated_dates_for_patient.
      3. Compute the date range we care about.
      4. Define missing_dates = target_dates - existing_curated_dates.
      5. For each missing date, fetch, transform, detect anomalies, and upload.
      6. Build recent anomalies and LLM explanation.
      7. Cache results.

    Args:
        days_back: Number of days to look back from today (default: 14).

    Returns:
        Dictionary containing:
            - "new_dates_processed": List of dates that were processed
            - "anomaly_count": Number of anomalies found
            - "recent_anomalies": List of dicts for recent anomalous days
            - "explanation": String explanation from LLM
            - "curated_blob_paths": List of blob paths for newly processed dates
    """
    # Step 1: Get patient_id from config
    patient_id = config.ultrahuman.patient_id
    if not patient_id:
        raise ValueError(
            "patient_id is not configured. Set ULTRAHUMAN_PATIENT_ID or ULTRAHUMAN_EMAIL in .env"
        )

    # Step 2: Get existing curated dates from storage
    storage_client = AzureStorageClient()
    existing_dates = set()
    try:
        existing_dates = set(storage_client.list_curated_dates_for_patient(patient_id))
        print(
            f"Info: Found {len(existing_dates)} existing curated dates for patient {patient_id}",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"Warning: Could not list existing dates from storage: {e}. "
            f"Will process all dates in range.",
            file=sys.stderr,
        )

    # Step 3: Compute target date range
    today = datetime.now().date()
    start_candidate = today - timedelta(days=days_back)

    # Step 4: Define target dates and missing dates
    target_dates = set()
    current_date = start_candidate
    while current_date <= today:
        target_dates.add(current_date)
        current_date += timedelta(days=1)

    missing_dates = sorted(target_dates - existing_dates)

    if not missing_dates:
        print(
            f"Info: No new dates to process. All dates in range [{start_candidate}, {today}] already exist in storage.",
            file=sys.stderr,
        )
        # Still need to build recent anomalies from existing data
        # For now, return empty result - could be enhanced to load from storage
        return {
            "new_dates_processed": [],
            "anomaly_count": 0,
            "recent_anomalies": [],
            "explanation": "No new data to process. All dates in range already exist.",
            "curated_blob_paths": [],
        }

    print(
        f"Info: Found {len(missing_dates)} missing dates to process: {missing_dates}",
        file=sys.stderr,
    )

    # Step 5: Process each missing date
    client = UltrahumanClient()
    processed_dfs = []
    curated_blob_paths = []
    new_dates_processed = []

    for target_date in missing_dates:
        enriched_df = _process_single_date(
            client, storage_client, patient_id, target_date
        )
        if enriched_df is not None and len(enriched_df) > 0:
            processed_dfs.append(enriched_df)
            new_dates_processed.append(target_date.strftime("%Y-%m-%d"))
            # Get blob path for this date
            date_str = target_date.strftime("%Y-%m-%d")
            blob_path = (
                f"curated/daily_metrics/patient_id={patient_id}/date={date_str}/metrics.parquet"
            )
            curated_blob_paths.append(blob_path)

    if not processed_dfs:
        print(
            f"Warning: No dates were successfully processed. Check API connectivity and data availability.",
            file=sys.stderr,
        )
        return {
            "new_dates_processed": [],
            "anomaly_count": 0,
            "recent_anomalies": [],
            "explanation": "No new data was successfully processed.",
            "curated_blob_paths": [],
        }

    print(
        f"Info: Successfully processed {len(processed_dfs)} date(s): {new_dates_processed}",
        file=sys.stderr,
    )

    # Step 6: Combine all processed DataFrames and get recent anomalies
    combined_df = pd.concat(processed_dfs, ignore_index=True)

    # Get last 5 anomalous rows
    anomalous_df = combined_df[combined_df["is_anomalous"] == True].tail(5)

    # If we don't have enough anomalies from new data, we could load more from storage
    # For now, use what we have
    recent_anomalies = anomalous_df.copy()
    recent_anomalies["date"] = recent_anomalies["date"].astype(str)
    recent_anomalies_list = recent_anomalies.to_dict("records")

    anomaly_count = len(recent_anomalies_list)
    print(
        f"Info: Detected {anomaly_count} anomalous day(s) in the newly processed data.",
        file=sys.stderr,
    )

    # Step 7: Generate explanation
    explanation = generate_explanation(recent_anomalies_list)
    if explanation and explanation != "No anomalies detected in the recent data.":
        print(
            f"Info: LLM explanation generated successfully ({len(explanation)} characters).",
            file=sys.stderr,
        )
    else:
        print(
            f"Info: No explanation generated (no anomalies or explanation service unavailable).",
            file=sys.stderr,
        )

    # Step 8: Cache results (similar to run_daily_pipeline)
    result = {
        "enriched": combined_df,
        "recent_anomalies": recent_anomalies_list,
        "explanation": explanation,
        "parquet_path": None,  # No local file for incremental
        "blob_path": curated_blob_paths[0] if curated_blob_paths else None,
        "new_dates_processed": new_dates_processed,
        "anomaly_count": len(recent_anomalies_list),
        "curated_blob_paths": curated_blob_paths,
    }

    # Cache in Redis (if available)
    try:
        cache_client = RedisCacheClient()
        cache_client.cache_pipeline_result(result)
    except Exception as e:
        print(f"Warning: Redis caching skipped: {e}", file=sys.stderr)

    # Always store in memory cache as fallback
    memory_cache.store_pipeline_result(result)

    print(
        f"Info: Incremental pipeline completed. Processed {len(new_dates_processed)} new date(s), "
        f"found {anomaly_count} anomaly/anomalies, cached {len(curated_blob_paths)} blob path(s).",
        file=sys.stderr,
    )

    return result
