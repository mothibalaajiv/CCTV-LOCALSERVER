import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    CLOUD_API_URL: str = "http://104.251.214.117:8000/api"
    CLOUD_API_KEY: Optional[str] = None
    HEALTH_CHECK_INTERVAL: int = 60
    DISCOVERY_INTERVAL: int = 300
    HEARTBEAT_INTERVAL: int = 30
    RETRY_COUNT: int = 3
    TIMEOUT_SECONDS: int = 10
    LOG_LEVEL: str = "INFO"
    LOCAL_SUBNET: Optional[str] = None
    CLOUD_SSH_HOST: Optional[str] = None
    CLOUD_SSH_USER: Optional[str] = None
    CLOUD_SSH_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
