"""UltraHuman API client module.

This module provides a client for interacting with the UltraHuman Partner API
to fetch health metrics data.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

from .config import config


class UltrahumanClient:
    """Client for interacting with the UltraHuman Partner API.

    This client wraps the UltraHuman Partner API endpoints to fetch health
    metrics data for specified date ranges.
    """

    def __init__(self, ultrahuman_config=None):
        """Initialize the UltraHuman client.

        Args:
            ultrahuman_config: Optional UltrahumanConfig instance. If not provided,
                uses the global config from src.config.
        """
        if ultrahuman_config is None:
            ultrahuman_config = config.ultrahuman

        self.api_base_url = ultrahuman_config.api_base_url.rstrip("/")
        self.api_key = ultrahuman_config.api_key
        self.email = ultrahuman_config.email
        self.patient_id = ultrahuman_config.patient_id

    def get_daily_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch health metrics for a date range (inclusive).

        Makes API calls for each day in the range [start_date, end_date] and
        aggregates all results into a single list.

        Args:
            start_date: Start date (inclusive) for fetching metrics.
            end_date: End date (inclusive) for fetching metrics.

        Returns:
            A list of metric records (dictionaries) aggregated across all days.

        Raises:
            RuntimeError: If the API response is invalid or cannot be parsed.
            requests.RequestException: If the HTTP request fails.
        """
        if start_date > end_date:
            return []

        all_metrics = []
        current_date = start_date

        while current_date <= end_date:
            daily_metrics = self._fetch_for_date(current_date)
            all_metrics.extend(daily_metrics)
            current_date += timedelta(days=1)

        return all_metrics

    def _fetch_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """Fetch health metrics for a specific date.

        Args:
            date: The date to fetch metrics for.

        Returns:
            A list of metric records (dictionaries) for the given date.

        Raises:
            RuntimeError: If the API response is invalid or cannot be parsed.
            requests.RequestException: If the HTTP request fails.
        """
        date_str = date.strftime("%Y-%m-%d")
        url = f"{self.api_base_url}/api/v1/metrics"

        params = {
            "email": self.email,
            "date": date_str,
        }

        headers = {
            "Authorization": self.api_key,
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"Failed to parse JSON response for date {date_str}: {e}"
                ) from e

            # Handle different response formats
            records = self._extract_records(data, date_str)
            return records

        except requests.RequestException as e:
            raise RuntimeError(
                f"API request failed for date {date_str}: {e}"
            ) from e

    def _extract_records(
        self, data: Any, date_str: str
    ) -> List[Dict[str, Any]]:
        """Extract records from API response.

        Handles multiple response formats:
        1. Direct list: [{"metric": "value"}, ...]
        2. Dict with "data.metric_data": {"data": {"metric_data": [...]}}
        3. Dict with "results" key: {"results": [{"metric": "value"}, ...]}
        4. Dict with "data.results": {"data": {"results": [...]}}

        Args:
            data: The parsed JSON response data.
            date_str: The date string (for error messages).

        Returns:
            A list of metric records.

        Raises:
            RuntimeError: If the response format is unexpected.
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Handle UltraHuman API format: {"data": {"metric_data": [...]}}
            if "data" in data:
                data_obj = data["data"]
                if isinstance(data_obj, dict):
                    if "metric_data" in data_obj:
                        metric_data = data_obj["metric_data"]
                        if isinstance(metric_data, list):
                            return metric_data
                    elif "results" in data_obj:
                        results = data_obj["results"]
                        if isinstance(results, list):
                            return results
            
            # Handle direct "results" key
            if "results" in data:
                results = data["results"]
                if isinstance(results, list):
                    return results
                else:
                    raise RuntimeError(
                        f"Expected 'results' to be a list for date {date_str}, "
                        f"got {type(results).__name__}"
                    )
            
            # If we get here, the format is unexpected
            available_keys = list(data.keys())
            raise RuntimeError(
                f"Response dict for date {date_str} does not contain "
                f"expected keys ('data.metric_data', 'data.results', or 'results'). "
                f"Available top-level keys: {available_keys}"
            )
        else:
            raise RuntimeError(
                f"Unexpected response type for date {date_str}: "
                f"expected list or dict, got {type(data).__name__}"
            )
