"""
Application settings using Pydantic for type safety and validation.
Supports multiple environments with YAML configuration files.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from typing import Annotated
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.constants import (
    DEFAULT_DIARIZATION_MODEL,
    DEFAULT_WHISPER_MODEL,
    MAX_UPLOAD_FILE_SIZE_BYTES,
    SUPPORTED_AUDIO_FORMATS,
    DEFAULT_TEMP_DIR,
)


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""
    
    url: str = Field(default="postgresql://localhost/audio_processor_dev", alias="DATABASE_URL")
    pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    echo_sql: bool = Field(default=False, alias="DB_ECHO_SQL")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class RedisSettings(BaseSettings):
    """Redis cache configuration."""
    
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    socket_connect_timeout: int = Field(default=10, alias="REDIS_CONNECT_TIMEOUT")
    socket_timeout: int = Field(default=10, alias="REDIS_SOCKET_TIMEOUT")
    max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class AuthSettings(BaseSettings):
    """Keycloak OAuth2 authentication configuration."""
    
    keycloak_url: str = Field(default="http://localhost:8080/auth", alias="KEYCLOAK_URL")
    realm: str = Field(default="audio-processor", alias="KEYCLOAK_REALM")
    client_id: str = Field(default="dev-client", alias="KEYCLOAK_CLIENT_ID")
    client_secret: str = Field(default="dev-secret", alias="KEYCLOAK_CLIENT_SECRET")
    algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    verify_signature: bool = Field(default=True, alias="JWT_VERIFY_SIGNATURE")
    verify_audience: bool = Field(default=True, alias="JWT_VERIFY_AUDIENCE")
    
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
    
    model_size: str = Field(default=DEFAULT_WHISPER_MODEL, alias="WHISPERX_MODEL_SIZE")
    device: str = Field(default="cuda", alias="WHISPERX_DEVICE")
    compute_type: str = Field(default="float16", alias="WHISPERX_COMPUTE_TYPE")
    language: str = Field(default="auto", alias="WHISPERX_LANGUAGE")
    batch_size: int = Field(default=8, alias="WHISPERX_BATCH_SIZE")
    return_char_alignments: bool = Field(default=False, alias="WHISPERX_CHAR_ALIGNMENTS")
    vad_onset: float = Field(default=0.5, alias="WHISPERX_VAD_ONSET")
    vad_offset: float = Field(default=0.363, alias="WHISPERX_VAD_OFFSET")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class DiarizationSettings(BaseSettings):
    """Speaker diarization configuration."""
    
    model_name: str = Field(default=DEFAULT_DIARIZATION_MODEL, alias="DIARIZATION_MODEL")
    device: str = Field(default="cuda", alias="DIARIZATION_DEVICE")
    use_auth_token: Optional[str] = Field(default=None, alias="HUGGINGFACE_TOKEN")
    min_speakers: Optional[int] = Field(default=None, alias="DIARIZATION_MIN_SPEAKERS")
    max_speakers: Optional[int] = Field(default=None, alias="DIARIZATION_MAX_SPEAKERS")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class CelerySettings(BaseSettings):
    """Celery background task configuration."""
    
    broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")
    task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", alias="CELERY_RESULT_SERIALIZER")
    accept_content: List[str] = Field(default=["json"], alias="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", alias="CELERY_TIMEZONE")
    enable_utc: bool = Field(default=True, alias="CELERY_ENABLE_UTC")
    worker_concurrency: int = Field(default=4, alias="CELERY_WORKER_CONCURRENCY")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class SummarizationSettings(BaseSettings):
    """Configuration for summarization service."""
    
    api_url: str = Field(default="http://localhost:8000/api/summarize", alias="SUMMARIZATION_API_URL")
    api_key: Optional[str] = Field(default=None, alias="SUMMARIZATION_API_KEY")
    model: str = Field(default="gpt-3.5-turbo", alias="SUMMARIZATION_MODEL")

    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class GraphDatabaseSettings(BaseSettings):
    """Graph database connection configuration."""
    
    type: str = Field(default="neo4j", alias="GRAPH_DATABASE_TYPE")  # neo4j, arangodb, etc.
    url: str = Field(default="bolt://localhost:7687", alias="GRAPH_DATABASE_URL")
    username: str = Field(default="neo4j", alias="GRAPH_DATABASE_USERNAME")
    password: str = Field(default="password", alias="GRAPH_DATABASE_PASSWORD")
    name: str = Field(default="neo4j", alias="GRAPH_DATABASE_NAME")
    
    # Connection pool settings
    max_connection_lifetime: int = Field(default=1800, alias="GRAPH_DATABASE_MAX_CONNECTION_LIFETIME")
    max_connection_pool_size: int = Field(default=50, alias="GRAPH_DATABASE_MAX_CONNECTION_POOL_SIZE")
    connection_acquisition_timeout: int = Field(default=30, alias="GRAPH_DATABASE_CONNECTION_ACQUISITION_TIMEOUT")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class GraphSettings(BaseSettings):
    """Graph processing configuration."""
    
    # Feature flag
    enabled: bool = Field(default=False, alias="GRAPH_ENABLED")
    
    # Database configuration
    database: GraphDatabaseSettings = Field(default_factory=GraphDatabaseSettings)
    
    # Processing configuration
    processing_batch_size: int = Field(default=100, alias="GRAPH_PROCESSING_BATCH_SIZE")
    processing_extraction_queue: str = Field(default="graph_extraction", alias="GRAPH_PROCESSING_EXTRACTION_QUEUE")
    
    # Topic extraction configuration
    topic_extraction_method: str = Field(default="keyword_matching", alias="GRAPH_TOPIC_EXTRACTION_METHOD")
    topic_keywords: Dict[str, List[str]] = Field(default={}, alias="GRAPH_TOPIC_KEYWORDS")
    
    # Entity extraction patterns
    entity_extraction_patterns: Dict[str, str] = Field(default={}, alias="GRAPH_ENTITY_EXTRACTION_PATTERNS")
    
    model_config = {
        "case_sensitive": False,
        "extra": "forbid",
    }


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    allowed_hosts: Union[str, List[str]] = Field(default=["*"], alias="ALLOWED_HOSTS")
    cors_origins: Union[str, List[str]] = Field(default=["*"], alias="CORS_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # Feature flags
    enable_audio_upload: bool = Field(default=True, alias="ENABLE_AUDIO_UPLOAD")
    enable_url_processing: bool = Field(default=True, alias="ENABLE_URL_PROCESSING")
    enable_translation: bool = Field(default=True, alias="ENABLE_TRANSLATION")
    enable_summarization: bool = Field(default=True, alias="ENABLE_SUMMARIZATION")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, alias="RATE_LIMIT_WINDOW")  # seconds
    
    # File processing
    max_file_size: int = Field(default=MAX_UPLOAD_FILE_SIZE_BYTES, alias="MAX_FILE_SIZE")
    supported_formats: Union[str, List[str]] = Field(
        default=SUPPORTED_AUDIO_FORMATS,
        alias="SUPPORTED_FORMATS"
    )
    temp_dir: str = Field(default=DEFAULT_TEMP_DIR, alias="TEMP_DIR")
    
    # Subsystem configurations (lazy loading to avoid env var issues)
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings())
    redis: RedisSettings = Field(default_factory=lambda: RedisSettings())
    auth: AuthSettings = Field(default_factory=lambda: AuthSettings())
    whisperx: WhisperXSettings = Field(default_factory=lambda: WhisperXSettings())
    diarization: DiarizationSettings = Field(default_factory=lambda: DiarizationSettings())
    celery: CelerySettings = Field(default_factory=lambda: CelerySettings())
    summarization: SummarizationSettings = Field(default_factory=lambda: SummarizationSettings())
    graph: GraphSettings = Field(default_factory=lambda: GraphSettings())
    
    @field_validator("cors_origins", "allowed_hosts", "supported_formats", mode="before")
    @classmethod
    def parse_comma_separated(cls, v):
        """Parse comma-separated environment variables to lists."""
        if isinstance(v, str):
            # Handle wildcard cases for CORS and allowed hosts
            if v.strip() == "*":
                return [v.strip()]
            return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
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
    
    model_config: SettingsConfigDict = {
        # Dynamic environment file selection
        "env_file": (
            ".env.test" if os.getenv("ENVIRONMENT") == "testing" 
            else ".env"
        ),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "populate_by_name": True,  # Replaces allow_population_by_field_name
        "extra": "ignore",  # Ignore extra fields from environment variables
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
