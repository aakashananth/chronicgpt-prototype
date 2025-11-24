"""Main entry point for running the health metrics pipeline."""

import json
import sys
from typing import Any, Dict

from .pipeline import run_daily_pipeline


def main() -> None:
    """Run the daily pipeline and print results."""
    try:
        # Run pipeline with 14 days lookback
        results = run_daily_pipeline(days_back=14)

        # Print recent anomalies
        print("=== Recent Anomalies ===")
        recent_anomalies = results.get("recent_anomalies", [])
        if recent_anomalies:
            for i, anomaly in enumerate(recent_anomalies, 1):
                print(f"\nAnomaly {i}:")
                # Format the anomaly dict nicely
                print(json.dumps(anomaly, indent=2, default=str))
        else:
            print("No recent anomalies detected.")

        # Print LLM explanation
        print("\n=== LLM Explanation ===")
        explanation = results.get("explanation", "No explanation available.")
        print(explanation)

        # Print Parquet file path
        print(f"\n=== Output File ===")
        parquet_path = results.get("parquet_path", "Unknown")
        print(f"Local Parquet file: {parquet_path}")

        # Print Azure Blob Storage path
        blob_path = results.get("blob_path")
        if blob_path:
            print(f"Azure Blob Storage path: {blob_path}")
        else:
            print("Azure Blob Storage: Not configured or upload skipped")

    except Exception as e:
        print(f"Error running pipeline: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
