from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ENV: str = "dev"
    
    # Postgres
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "insightblog"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Vespa
    VESPA_HOST: str = "localhost"
    VESPA_PORT: int = 8080

    # Auth
    SECRET_KEY: str = "supersecretkeychangeinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Admin
    ADMIN_EMAIL: str = "admin@insightblog.com"
    ADMIN_PASSWORD: str = "admin123"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_FILENAME: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 10

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def VESPA_URL(self) -> str:
        return f"http://{self.VESPA_HOST}:{self.VESPA_PORT}"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
