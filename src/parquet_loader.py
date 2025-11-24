"""Helper functions to load data from parquet files."""

import os
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import config


def load_from_parquet(parquet_path: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Load enriched metrics from parquet file.

    Args:
        parquet_path: Path to parquet file. If None, uses default path from config.

    Returns:
        DataFrame with enriched metrics, or None if file doesn't exist.
    """
    if parquet_path is None:
        parquet_path = os.path.join(config.storage.data_dir, "daily_metrics_enriched.parquet")

    if not os.path.exists(parquet_path):
        return None

    try:
        df = pd.read_parquet(parquet_path)
        return df
    except Exception:
        return None


def extract_metrics_from_parquet(parquet_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Extract metrics summary from parquet file.

    Args:
        parquet_path: Path to parquet file. If None, uses default path from config.

    Returns:
        Dictionary with metrics summary, or None if file doesn't exist.
    """
    df = load_from_parquet(parquet_path)
    if df is None or df.empty:
        return None

    # Convert date to string for JSON serialization
    df_copy = df.copy()
    if "date" in df_copy.columns:
        df_copy["date"] = df_copy["date"].astype(str)

    # Return a summary structure
    return {
        "total_records": len(df),
        "columns": list(df.columns),
        "date_range": {
            "start": str(df["date"].min()) if "date" in df.columns else None,
            "end": str(df["date"].max()) if "date" in df.columns else None,
        },
    }


def extract_anomalies_from_parquet(parquet_path: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Extract recent anomalies from parquet file.

    Args:
        parquet_path: Path to parquet file. If None, uses default path from config.

    Returns:
        List of anomaly dictionaries (last 5 anomalous rows), or None if file doesn't exist.
    """
    df = load_from_parquet(parquet_path)
    if df is None or df.empty:
        return None

    # Check if anomaly columns exist
    if "is_anomalous" not in df.columns:
        return None

    # Get last 5 anomalous rows
    anomalous_df = df[df["is_anomalous"] == True].tail(5)
    if anomalous_df.empty:
        return None

    # Convert to list of dicts
    result_df = anomalous_df.copy()
    if "date" in result_df.columns:
        result_df["date"] = result_df["date"].astype(str)

    return result_df.to_dict("records")


def get_parquet_path() -> Optional[str]:
    """Get the default parquet file path.

    Returns:
        Path to parquet file, or None if directory doesn't exist.
    """
    parquet_path = os.path.join(config.storage.data_dir, "daily_metrics_enriched.parquet")
    if os.path.exists(parquet_path):
        return parquet_path
    return None

