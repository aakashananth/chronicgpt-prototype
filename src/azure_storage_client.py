"""Azure Blob Storage client module for uploading health metrics data."""

import io
import json
import os
import sys
from datetime import date, datetime
from typing import List, Optional

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from .config import config


class AzureStorageClient:
    """Client for interacting with Azure Blob Storage."""

    def __init__(self, azure_storage_config=None):
        """Initialize the Azure Storage client.

        Args:
            azure_storage_config: Optional AzureStorageConfig instance. If not provided,
                uses the global config from src.config.
        """
        if azure_storage_config is None:
            azure_storage_config = config.azure_storage

        self.account_name = azure_storage_config.account_name
        self.account_key = azure_storage_config.account_key
        self.container_name = azure_storage_config.container_name
        self._blob_service_client = None

    def _get_blob_service_client(self) -> BlobServiceClient:
        """Get or create the BlobServiceClient.

        Returns:
            BlobServiceClient instance.

        Raises:
            ValueError: If Azure Storage is not properly configured.
        """
        if not self.account_name or not self.account_key:
            raise ValueError(
                "Azure Storage is not configured. "
                "Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY in .env"
            )

        if self._blob_service_client is None:
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key};"
                f"EndpointSuffix=core.windows.net"
            )
            self._blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )

        return self._blob_service_client

    def upload_parquet_file(
        self, local_file_path: str, blob_prefix: str = "curated/daily_metrics"
    ) -> Optional[str]:
        """Upload a Parquet file to Azure Blob Storage.

        Args:
            local_file_path: Path to the local Parquet file to upload.
            blob_prefix: Prefix path in the blob container (default: "curated/daily_metrics").

        Returns:
            Blob path if upload successful, None if Azure Storage is not configured.

        Raises:
            RuntimeError: If upload fails.
            ValueError: If Azure Storage is not properly configured.
        """
        # Check if Azure Storage is configured
        if not self.account_name or not self.account_key:
            return None

        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        try:
            # Get blob service client
            blob_service_client = self._get_blob_service_client()

            # Generate blob name with date suffix
            file_name = os.path.basename(local_file_path)
            if "daily_metrics_enriched" in file_name:
                # Format: curated/daily_metrics/daily_metrics_enriched_YYYY-MM-DD.parquet
                today = datetime.now().strftime("%Y-%m-%d")
                blob_name = f"{blob_prefix}/daily_metrics_enriched_{today}.parquet"
            else:
                blob_name = f"{blob_prefix}/{file_name}"

            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # Upload file
            with open(local_file_path, "rb") as data:
                container_client.upload_blob(
                    name=blob_name, data=data, overwrite=True
                )

            return blob_name

        except ValueError:
            # Re-raise ValueError as-is (configuration errors)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload to Azure Blob Storage: {e}. "
                f"Check your Azure Storage configuration and network connectivity."
            ) from e

    def upload_raw_metrics(
        self, patient_id: str, date_obj: date, raw_json: dict
    ) -> Optional[str]:
        """Upload raw Ultrahuman response for a given patient and date.

        Path format:
            raw/ultrahuman/patient_id={patient_id}/date={YYYY-MM-DD}/metrics_raw.json

        Args:
            patient_id: Patient identifier.
            date_obj: Date object for the metrics.
            raw_json: Raw JSON response dictionary to upload.

        Returns:
            Blob path if upload successful, None if Azure Storage is not configured or blob already exists.

        Raises:
            RuntimeError: If upload fails (other than already exists).
            ValueError: If Azure Storage is not properly configured.
        """
        # Check if Azure Storage is configured
        if not self.account_name or not self.account_key:
            return None

        try:
            # Get blob service client
            blob_service_client = self._get_blob_service_client()

            # Generate blob name with partitioned path
            date_str = date_obj.strftime("%Y-%m-%d")
            blob_name = (
                f"raw/ultrahuman/patient_id={patient_id}/date={date_str}/metrics_raw.json"
            )

            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # Serialize JSON to bytes
            json_bytes = json.dumps(raw_json, default=str).encode("utf-8")

            # Upload blob with overwrite=False
            container_client.upload_blob(
                name=blob_name, data=json_bytes, overwrite=False
            )

            return blob_name

        except ResourceExistsError:
            # Blob already exists - this is expected for idempotent operations
            date_str = date_obj.strftime("%Y-%m-%d")
            blob_name = (
                f"raw/ultrahuman/patient_id={patient_id}/date={date_str}/metrics_raw.json"
            )
            print(
                f"Info: Raw metrics already exist for patient {patient_id}, date {date_str}. Skipping upload.",
                file=sys.stderr,
            )
            return None
        except ValueError:
            # Re-raise ValueError as-is (configuration errors)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload raw metrics to Azure Blob Storage: {e}. "
                f"Check your Azure Storage configuration and network connectivity."
            ) from e

    def upload_curated_daily_metrics(
        self, patient_id: str, date_obj: date, df: pd.DataFrame
    ) -> Optional[str]:
        """Upload a single-row DataFrame of enriched daily metrics for a given patient and date.

        Path format:
            curated/daily_metrics/patient_id={patient_id}/date={YYYY-MM-DD}/metrics.parquet

        Args:
            patient_id: Patient identifier.
            date_obj: Date object for the metrics.
            df: Single-row DataFrame with enriched metrics.

        Returns:
            Blob path if upload successful, None if Azure Storage is not configured or blob already exists.

        Raises:
            RuntimeError: If upload fails (other than already exists).
            ValueError: If Azure Storage is not properly configured or DataFrame is not single-row.
        """
        # Check if Azure Storage is configured
        if not self.account_name or not self.account_key:
            return None

        # Validate DataFrame
        if len(df) != 1:
            raise ValueError(
                f"Expected single-row DataFrame, got {len(df)} rows. "
                f"This method should only be called with one row at a time."
            )

        try:
            # Get blob service client
            blob_service_client = self._get_blob_service_client()

            # Generate blob name with partitioned path
            date_str = date_obj.strftime("%Y-%m-%d")
            blob_name = (
                f"curated/daily_metrics/patient_id={patient_id}/date={date_str}/metrics.parquet"
            )

            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # Convert DataFrame to Parquet bytes
            parquet_buffer = io.BytesIO()
            df.to_parquet(parquet_buffer, index=False)
            parquet_buffer.seek(0)

            # Upload blob with overwrite=False
            container_client.upload_blob(
                name=blob_name, data=parquet_buffer.read(), overwrite=False
            )

            return blob_name

        except ResourceExistsError:
            # Blob already exists - this is expected for idempotent operations
            date_str = date_obj.strftime("%Y-%m-%d")
            blob_name = (
                f"curated/daily_metrics/patient_id={patient_id}/date={date_str}/metrics.parquet"
            )
            print(
                f"Info: Curated metrics already exist for patient {patient_id}, date {date_str}. Skipping upload.",
                file=sys.stderr,
            )
            return None
        except ValueError:
            # Re-raise ValueError as-is (configuration errors or validation errors)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload curated metrics to Azure Blob Storage: {e}. "
                f"Check your Azure Storage configuration and network connectivity."
            ) from e

    def list_curated_dates_for_patient(self, patient_id: str) -> List[date]:
        """List all dates for which curated daily metrics exist for this patient.

        Lists blobs under the prefix:
            curated/daily_metrics/patient_id={patient_id}/

        Parses the {YYYY-MM-DD} date component from the path
        (e.g. .../date=2025-11-21/metrics.parquet).

        Args:
            patient_id: Patient identifier.

        Returns:
            Sorted list of unique datetime.date objects.

        Raises:
            ValueError: If Azure Storage is not properly configured.
            RuntimeError: If listing fails.
        """
        # Check if Azure Storage is configured
        if not self.account_name or not self.account_key:
            return []

        try:
            # Get blob service client
            blob_service_client = self._get_blob_service_client()

            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # List blobs with prefix
            prefix = f"curated/daily_metrics/patient_id={patient_id}/"
            blobs = container_client.list_blobs(name_starts_with=prefix)

            # Extract dates from blob paths
            dates = []
            for blob in blobs:
                # Parse date from path: curated/daily_metrics/patient_id={patient_id}/date={YYYY-MM-DD}/metrics.parquet
                blob_name = blob.name
                if "/date=" in blob_name:
                    try:
                        # Extract date string from path
                        date_part = blob_name.split("/date=")[1].split("/")[0]
                        date_obj = datetime.strptime(date_part, "%Y-%m-%d").date()
                        dates.append(date_obj)
                    except (ValueError, IndexError) as e:
                        # Skip invalid date formats
                        print(
                            f"Warning: Could not parse date from blob path {blob_name}: {e}",
                            file=sys.stderr,
                        )
                        continue

            # Return sorted unique dates
            return sorted(set(dates))

        except ValueError:
            # Re-raise ValueError as-is (configuration errors)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to list curated dates for patient {patient_id}: {e}. "
                f"Check your Azure Storage configuration and network connectivity."
            ) from e

    def load_curated_metrics_for_date_range(
        self, patient_id: str, start_date: date, end_date: date
    ) -> pd.DataFrame:
        """Load curated daily metrics for a date range from Azure Blob Storage.

        Loads all parquet files for the patient within the specified date range
        and combines them into a single DataFrame.

        Args:
            patient_id: Patient identifier.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            DataFrame with all metrics for the date range, sorted by date.
            Empty DataFrame if no data found or Azure Storage is not configured.

        Raises:
            ValueError: If Azure Storage is not properly configured.
            RuntimeError: If loading fails.
        """
        # Check if Azure Storage is configured
        if not self.account_name or not self.account_key:
            return pd.DataFrame()

        try:
            # Get blob service client
            blob_service_client = self._get_blob_service_client()

            # Get container client
            container_client = blob_service_client.get_container_client(
                self.container_name
            )

            # List blobs with prefix
            prefix = f"curated/daily_metrics/patient_id={patient_id}/"
            blobs = container_client.list_blobs(name_starts_with=prefix)

            # Load dataframes for dates in range
            dataframes = []
            for blob in blobs:
                # Parse date from path: curated/daily_metrics/patient_id={patient_id}/date={YYYY-MM-DD}/metrics.parquet
                blob_name = blob.name
                if "/date=" in blob_name:
                    try:
                        # Extract date string from path
                        date_part = blob_name.split("/date=")[1].split("/")[0]
                        blob_date = datetime.strptime(date_part, "%Y-%m-%d").date()

                        # Check if date is in range
                        if start_date <= blob_date <= end_date:
                            # Download blob and load as DataFrame
                            blob_client = container_client.get_blob_client(blob_name)
                            
                            # Check blob size first - skip empty/corrupted files
                            blob_properties = blob_client.get_blob_properties()
                            if blob_properties.size == 0:
                                print(
                                    f"Warning: Skipping empty blob {blob_name} (0 bytes)",
                                    file=sys.stderr,
                                )
                                continue
                            
                            blob_data = blob_client.download_blob().readall()
                            
                            # Double-check data size
                            if len(blob_data) == 0:
                                print(
                                    f"Warning: Skipping empty blob {blob_name} (no data)",
                                    file=sys.stderr,
                                )
                                continue
                            
                            # Try to read Parquet file
                            try:
                                df = pd.read_parquet(io.BytesIO(blob_data))
                                # Skip if DataFrame is empty
                                if df.empty:
                                    print(
                                        f"Warning: Skipping empty DataFrame from blob {blob_name}",
                                        file=sys.stderr,
                                    )
                                    continue
                                dataframes.append(df)
                            except Exception as parquet_error:
                                print(
                                    f"Warning: Could not read Parquet file {blob_name}: {parquet_error}. Skipping.",
                                    file=sys.stderr,
                                )
                                continue
                    except (ValueError, IndexError) as e:
                        # Skip invalid date formats
                        print(
                            f"Warning: Could not parse date from blob path {blob_name}: {e}",
                            file=sys.stderr,
                        )
                        continue
                    except Exception as e:
                        print(
                            f"Warning: Could not load blob {blob_name}: {e}. Skipping.",
                            file=sys.stderr,
                        )
                        continue

            # Combine all dataframes
            if not dataframes:
                return pd.DataFrame()

            combined_df = pd.concat(dataframes, ignore_index=True)

            # Ensure date column exists and sort by date
            if "date" in combined_df.columns:
                # Convert date column to date type if needed
                if combined_df["date"].dtype == "object":
                    combined_df["date"] = pd.to_datetime(combined_df["date"]).dt.date
                combined_df = combined_df.sort_values("date").reset_index(drop=True)

            return combined_df

        except ValueError:
            # Re-raise ValueError as-is (configuration errors)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to load curated metrics for patient {patient_id} "
                f"from {start_date} to {end_date}: {e}. "
                f"Check your Azure Storage configuration and network connectivity."
            ) from e

