"""Configuration module for health metrics LLM prototype."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class UltrahumanConfig:
    """Configuration for UltraHuman API client."""

    api_base_url: str
    api_key: str  # The Authorization token (no "Bearer" prefix)
    email: str
    patient_id: Optional[str]  # Patient identifier (defaults to email if not set)

    @classmethod
    def from_env(cls) -> "UltrahumanConfig":
        """Create UltrahumanConfig from environment variables."""
        email = os.getenv("ULTRAHUMAN_EMAIL", "")
        # Use ULTRAHUMAN_PATIENT_ID if set, otherwise default to email
        patient_id = os.getenv("ULTRAHUMAN_PATIENT_ID", email)
        return cls(
            api_base_url=os.getenv("ULTRAHUMAN_API_BASE_URL", ""),
            api_key=os.getenv("ULTRAHUMAN_API_KEY", ""),
            email=email,
            patient_id=patient_id,
        )


@dataclass
class AzureOpenAIConfig:
    """Configuration for Azure OpenAI service."""

    endpoint: str
    api_key: str
    deployment_name: str
    api_version: str

    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """Create AzureOpenAIConfig from environment variables."""
        return cls(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        )


@dataclass
class LocalStorageConfig:
    """Configuration for local data storage."""

    data_dir: str

    @classmethod
    def from_env(cls) -> "LocalStorageConfig":
        """Create LocalStorageConfig from environment variables."""
        return cls(
            data_dir=os.getenv("LOCAL_DATA_DIR", "data"),
        )


@dataclass
class AzureStorageConfig:
    """Configuration for Azure Blob Storage."""

    account_name: str
    account_key: str
    container_name: str

    @classmethod
    def from_env(cls) -> "AzureStorageConfig":
        """Create AzureStorageConfig from environment variables."""
        return cls(
            account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME", ""),
            account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY", ""),
            container_name=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "health-metrics"),
        )


@dataclass
class RedisConfig:
    """Configuration for Azure Cache for Redis."""

    host: str
    port: int
    password: str
    ssl: bool

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create RedisConfig from environment variables."""
        # Support both REDIS_SSL and REDIS_USE_SSL for backward compatibility
        ssl_value = os.getenv("REDIS_SSL") or os.getenv("REDIS_USE_SSL", "true")
        return cls(
            host=os.getenv("REDIS_HOST", ""),
            port=int(os.getenv("REDIS_PORT", "6380")),
            password=os.getenv("REDIS_ACCESS_KEY", ""),
            ssl=ssl_value.lower() == "true",
        )


@dataclass
class AppConfig:
    """Main application configuration aggregating all sub-configurations."""

    ultrahuman: UltrahumanConfig
    azure_openai: AzureOpenAIConfig
    storage: LocalStorageConfig
    azure_storage: AzureStorageConfig
    redis: RedisConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create AppConfig from environment variables."""
        return cls(
            ultrahuman=UltrahumanConfig.from_env(),
            azure_openai=AzureOpenAIConfig.from_env(),
            storage=LocalStorageConfig.from_env(),
            azure_storage=AzureStorageConfig.from_env(),
            redis=RedisConfig.from_env(),
        )


# Global configuration instance
config = AppConfig.from_env()
