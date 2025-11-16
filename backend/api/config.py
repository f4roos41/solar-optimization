"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://solar_user:solar_password@localhost:5432/solar_platform"

    # Message Broker
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "rpc://"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_DATA_LAKE_BUCKET: str = "solar-platform-data-lake"
    S3_RESULTS_BUCKET: str = "solar-platform-results"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Processing Limits
    MAX_AOI_AREA_KM2: int = 10000
    DEFAULT_RASTER_RESOLUTION: int = 90
    GDAL_CACHEMAX: int = 512
    NUM_WORKER_PROCESSES: int = 4

    # Job Configuration
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3600
    CELERY_TASK_TIME_LIMIT: int = 7200
    MAX_CONCURRENT_JOBS_PER_USER: int = 3

    # Feature Flags
    ENABLE_3D_VISUALIZATION: bool = True
    ENABLE_SHADOW_ANALYSIS: bool = True
    ENABLE_PV_SIMULATION: bool = True
    ENABLE_FINANCIAL_ANALYSIS: bool = True
    ENABLE_PREMIUM_DATA_SOURCES: bool = False

    # External APIs
    SOLARGIS_API_KEY: str = ""
    SOLCAST_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
