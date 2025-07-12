import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    # API Configuration
    API_TITLE: str = "Auth Service"
    API_DESCRIPTION: str = "Authentication and Authorization Service"
    API_VERSION: str = "1.0.0"

    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "very-secret-key-should-be-in-env-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Telemetry Configuration
    ZIPKIN_URL: str = os.getenv("ZIPKIN_URL", "http://localhost:9411")
    TELEMETRY_ENABLED: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # Database Configuration (would be used in a real implementation)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/authdb")

    # RabbitMQ Configuration (would be used in a real implementation)
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings as a singleton
    """
    return Settings()
