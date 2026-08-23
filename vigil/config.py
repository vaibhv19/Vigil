from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Environment
    ENV: str = Field(default="development", description="Application environment (development/production/test)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="Connection URL for the PostgreSQL database"
    )
    
    # Docker/Sandbox defaults
    DOCKER_HOST_URL: str = Field(
        default="unix:///var/run/docker.sock",
        description="Docker daemon connection path"
    )
    WORKSPACE_BASE_DIR: str = Field(
        ...,
        description="Absolute path on the host for mounting temp workspaces"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
