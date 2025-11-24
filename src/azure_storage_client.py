"""Azure Blob Storage client module for uploading health metrics data."""

import os
from datetime import datetime
from typing import Optional

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

