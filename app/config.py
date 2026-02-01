"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "sync-async-api"
    debug: bool = False
    
    # Database
    database_path: str = "./data/requests.db"
    
    # Sync Endpoint
    max_sync_concurrency: int = 10
    work_timeout_seconds: int = 30
    
    # Async Workers
    num_workers: int = 5
    max_queue_size: int = 100
    callback_timeout_seconds: int = 10
    max_callback_retries: int = 3
    retry_backoff_base: int = 2
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    max_payload_size_kb: int = 100
    
    # Security
    allowed_callback_schemes: list[str] = ["http", "https"]
    block_private_ips: bool = True
    block_localhost: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
