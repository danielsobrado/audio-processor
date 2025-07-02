"""
Application settings using Pydantic for type safety and validation.
Supports multiple environments with YAML configuration files.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from typing import Annotated
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from app.utils.constants import (
    DEFAULT_DIARIZATION_MODEL,
    DEFAULT_WHISPER_MODEL,
    MAX_UPLOAD_FILE_SIZE_BYTES,
    SUPPORTED_AUDIO_FORMATS,
    DEFAULT_TEMP_DIR,
)


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""
    
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    echo_sql: bool = Field(default=False, env="DB_ECHO_SQL")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class RedisSettings(BaseSettings):
    """Redis cache configuration."""
    
    url: str = Field(..., env="REDIS_URL")
    socket_connect_timeout: int = Field(default=10, env="REDIS_CONNECT_TIMEOUT")
    socket_timeout: int = Field(default=10, env="REDIS_SOCKET_TIMEOUT")
    max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class AuthSettings(BaseSettings):
    """Keycloak OAuth2 authentication configuration."""
    
    keycloak_url: str = Field(..., env="KEYCLOAK_URL")
    realm: str = Field(..., env="KEYCLOAK_REALM")
    client_id: str = Field(..., env="KEYCLOAK_CLIENT_ID")
    client_secret: str = Field(..., env="KEYCLOAK_CLIENT_SECRET")
    algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    verify_signature: bool = Field(default=True, env="JWT_VERIFY_SIGNATURE")
    verify_audience: bool = Field(default=True, env="JWT_VERIFY_AUDIENCE")
    
    @property
    def issuer_url(self) -> str:
        """Keycloak issuer URL."""
        return f"{self.keycloak_url}/realms/{self.realm}"
    
    @property
    def jwks_url(self) -> str:
        """Keycloak JWKS URL for public key retrieval."""
        return f"{self.issuer_url}/protocol/openid-connect/certs"

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class WhisperXSettings(BaseSettings):
    """WhisperX model configuration."""
    
    model_size: str = Field(default=DEFAULT_WHISPER_MODEL, env="WHISPERX_MODEL_SIZE")
    device: str = Field(default="cuda", env="WHISPERX_DEVICE")
    compute_type: str = Field(default="float16", env="WHISPERX_COMPUTE_TYPE")
    language: str = Field(default="auto", env="WHISPERX_LANGUAGE")
    batch_size: int = Field(default=8, env="WHISPERX_BATCH_SIZE")
    return_char_alignments: bool = Field(default=False, env="WHISPERX_CHAR_ALIGNMENTS")
    vad_onset: float = Field(default=0.5, env="WHISPERX_VAD_ONSET")
    vad_offset: float = Field(default=0.363, env="WHISPERX_VAD_OFFSET")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class DiarizationSettings(BaseSettings):
    """Speaker diarization configuration."""
    
    model_name: str = Field(default=DEFAULT_DIARIZATION_MODEL, env="DIARIZATION_MODEL")
    device: str = Field(default="cuda", env="DIARIZATION_DEVICE")
    use_auth_token: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")
    min_speakers: Optional[int] = Field(default=None, env="DIARIZATION_MIN_SPEAKERS")
    max_speakers: Optional[int] = Field(default=None, env="DIARIZATION_MAX_SPEAKERS")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class CelerySettings(BaseSettings):
    """Celery background task configuration."""
    
    broker_url: str = Field(..., env="CELERY_BROKER_URL")
    result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    accept_content: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")
    enable_utc: bool = Field(default=True, env="CELERY_ENABLE_UTC")
    worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class SummarizationSettings(BaseSettings):
    """Configuration for summarization service."""
    
    api_url: str = Field(..., env="SUMMARIZATION_API_URL")
    api_key: Optional[str] = Field(None, env="SUMMARIZATION_API_KEY")
    model: str = Field("gpt-3.5-turbo", env="SUMMARIZATION_MODEL")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Feature flags
    enable_audio_upload: bool = Field(default=True, env="ENABLE_AUDIO_UPLOAD")
    enable_url_processing: bool = Field(default=True, env="ENABLE_URL_PROCESSING")
    enable_translation: bool = Field(default=True, env="ENABLE_TRANSLATION")
    enable_summarization: bool = Field(default=True, env="ENABLE_SUMMARIZATION")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # seconds
    
    # File processing
    max_file_size: int = Field(default=MAX_UPLOAD_FILE_SIZE_BYTES, env="MAX_FILE_SIZE")
    supported_formats: List[str] = Field(
        default=SUPPORTED_AUDIO_FORMATS,
        env="SUPPORTED_FORMATS"
    )
    temp_dir: str = Field(default=DEFAULT_TEMP_DIR, env="TEMP_DIR")
    
    # Subsystem configurations (lazy loading to avoid env var issues)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    whisperx: WhisperXSettings = Field(default_factory=WhisperXSettings)
    diarization: DiarizationSettings = Field(default_factory=DiarizationSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    summarization: SummarizationSettings = Field(default_factory=SummarizationSettings)
    
    @field_validator("cors_origins", "allowed_hosts", "supported_formats", mode="before")
    @classmethod
    def parse_comma_separated(cls, v):
        """Parse comma-separated environment variables to lists."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_environments = ["development", "uat", "production", "testing"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    model_config = {
        # Dynamic environment file selection
        "env_file": (
            ".env.test" if os.getenv("ENVIRONMENT") == "testing" 
            else ".env"
        ),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_by_name": True,  # Replaces allow_population_by_field_name
    }


def load_yaml_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")


def get_config_path() -> Path:
    """Get configuration file path based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    config_dir = Path(__file__).parent.parent.parent / "config"
    config_file = config_dir / f"{env}.yaml"
    
    # Fallback to local.yaml for development
    if not config_file.exists() and env == "development":
        config_file = config_dir / "local.yaml"
    
    return config_file


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    Combines environment variables with YAML configuration.
    """
    # Load YAML configuration
    config_path = get_config_path()
    yaml_config = load_yaml_config(config_path)
    
    # Create settings instance with YAML overrides
    settings_dict = {}
    
    # Flatten nested YAML structure for Pydantic
    for key, value in yaml_config.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                env_key = f"{key}_{subkey}".upper()
                settings_dict[env_key] = subvalue
        else:
            settings_dict[key.upper()] = value
    
    # Update environment with YAML values (if not already set)
    for key, value in settings_dict.items():
        if key not in os.environ:
            os.environ[key] = str(value)
    
    return Settings()


def get_test_settings(**overrides) -> Settings:
    """
    Get settings for testing without caching.
    Allows for per-test configuration overrides.
    
    Args:
        **overrides: Settings to override for this test
    
    Returns:
        Fresh Settings instance without caching
    """
    # Set test environment variables
    test_env = {
        "ENVIRONMENT": "testing",
        "DEBUG": "True",
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/15",
        **overrides
    }
    
    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = str(value)
    
    try:
        # Create fresh settings instance
        settings = Settings()
        return settings
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
