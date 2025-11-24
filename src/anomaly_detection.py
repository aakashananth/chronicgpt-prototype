"""Anomaly detection module for health metrics."""

from typing import Optional

import numpy as np
import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Detect anomalies in health metrics data.

    This function analyzes health metrics data and identifies anomalous patterns
    using rolling baseline comparisons and threshold-based flags.

    Args:
        df: DataFrame with health metrics. Expected columns:
            - date: Date column (will be converted to date type)
            - hrv: Heart rate variability values
            - resting_hr: Resting heart rate values
            - sleep_score: Sleep quality score (0-100)
            - steps: Daily step count
            Optional columns (if present, will be analyzed):
            - recovery_index: Recovery index value
            - movement_index: Movement index value
            - vo2_max: VO2 max value
            - active_minutes: Active minutes count

    Returns:
        DataFrame enriched with anomaly detection columns:
            - hrv_baseline: 7-day rolling median of HRV
            - rhr_baseline: 7-day rolling median of resting HR
            - low_hrv_flag: True if HRV < baseline * 0.7
            - high_rhr_flag: True if resting HR > baseline * 1.15
            - low_sleep_flag: True if sleep_score < 60
            - low_recovery_flag: True if recovery_index < 50 (if available)
            - low_movement_flag: True if movement_index < 40 (if available)
            - is_anomalous: True if any flag is True
            - anomaly_severity: Sum of all flags (0-6, depending on available metrics)

    Raises:
        ValueError: If required columns are missing from the DataFrame.
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()

    # Validate required columns
    required_columns = ["date", "hrv", "resting_hr", "sleep_score", "steps"]
    missing_columns = [col for col in required_columns if col not in result_df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Required columns: {required_columns}"
        )

    # Convert date to date type (not datetime)
    result_df["date"] = pd.to_datetime(result_df["date"]).dt.date

    # Sort by date to ensure proper rolling window calculation
    result_df = result_df.sort_values("date").reset_index(drop=True)

    # Compute 7-day rolling medians for baselines
    result_df["hrv_baseline"] = (
        result_df["hrv"].rolling(window=7, min_periods=1).median()
    )
    result_df["rhr_baseline"] = (
        result_df["resting_hr"].rolling(window=7, min_periods=1).median()
    )

    # Core anomaly flags
    result_df["low_hrv_flag"] = result_df["hrv"] < (result_df["hrv_baseline"] * 0.7)
    result_df["high_rhr_flag"] = (
        result_df["resting_hr"] > (result_df["rhr_baseline"] * 1.15)
    )
    result_df["low_sleep_flag"] = result_df["sleep_score"] < 60

    # Additional analytics for optional fields
    flag_columns = ["low_hrv_flag", "high_rhr_flag", "low_sleep_flag"]

    # Recovery index analysis (if available)
    if "recovery_index" in result_df.columns:
        recovery_baseline = (
            result_df["recovery_index"].rolling(window=7, min_periods=1).median()
        )
        result_df["recovery_baseline"] = recovery_baseline
        result_df["low_recovery_flag"] = result_df["recovery_index"] < 50
        flag_columns.append("low_recovery_flag")

    # Movement index analysis (if available)
    if "movement_index" in result_df.columns:
        movement_baseline = (
            result_df["movement_index"].rolling(window=7, min_periods=1).median()
        )
        result_df["movement_baseline"] = movement_baseline
        result_df["low_movement_flag"] = result_df["movement_index"] < 40
        flag_columns.append("low_movement_flag")

    # Steps analysis (low activity detection)
    if "steps" in result_df.columns:
        steps_baseline = (
            result_df["steps"].rolling(window=7, min_periods=1).median()
        )
        result_df["steps_baseline"] = steps_baseline
        result_df["low_steps_flag"] = result_df["steps"] < (steps_baseline * 0.6)
        flag_columns.append("low_steps_flag")

    # Active minutes analysis (if available)
    if "active_minutes" in result_df.columns:
        active_baseline = (
            result_df["active_minutes"].rolling(window=7, min_periods=1).median()
        )
        result_df["active_baseline"] = active_baseline
        result_df["low_active_flag"] = result_df["active_minutes"] < (
            active_baseline * 0.6
        )
        flag_columns.append("low_active_flag")

    # VO2 Max analysis (if available)
    if "vo2_max" in result_df.columns:
        vo2_baseline = (
            result_df["vo2_max"].rolling(window=7, min_periods=1).median()
        )
        result_df["vo2_baseline"] = vo2_baseline
        result_df["low_vo2_flag"] = result_df["vo2_max"] < (vo2_baseline * 0.9)
        flag_columns.append("low_vo2_flag")

    # Compute is_anomalous: True if any flag is True
    result_df["is_anomalous"] = result_df[flag_columns].any(axis=1)

    # Compute anomaly_severity: sum of all flags as integers
    result_df["anomaly_severity"] = (
        result_df[flag_columns].astype(int).sum(axis=1)
    )

    return result_df
