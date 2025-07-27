# ============================================================================
# app/config/settings.py - Application Configuration
# ============================================================================

import os
from typing import List, Optional, Dict, Any
# from pydantic import BaseSettings, validator
from functools import lru_cache


# # class Settings(BaseSettings):
#     """Application settings with environment variable support"""

# Basic Application Settings
APP_NAME: str = "FarmBot Pro"
APP_VERSION: str = "2.0.0"
ENVIRONMENT: str = "development"
DEBUG: bool = False

# API Configuration
API_V1_STR: str = "/api/v1"
HOST: str = "0.0.0.0"
PORT: int = 8000

# Security Settings
SECRET_KEY: str = "farmbot-super-secret-key-change-in-production"
JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

# # Database Configuration
# DATABASE_URL: str = "postgresql://farmbot:password@localhost/farmbot_prod"
# DATABASE_POOL_SIZE: int = 10
# DATABASE_MAX_OVERFLOW: int = 20

# # Redis Configuration
# REDIS_URL: str = "redis://localhost:6379"
# REDIS_PASSWORD: Optional[str] = None
# CACHE_TTL: int = 300  # 5 minutes

# External API Keys
GOOGLE_AI_API_KEY: str = "AIzaSyBdB-hJP98rzrxHpzGvDY5GusJa6jqtJQ4"
OPENWEATHER_API_KEY: str = "e1922be5d43231001db3bc8f8ec70252"
DATA_GOV_API_KEY: str = '579b464db66ec23bdd00000144dbb7c15318403c464dffb5257ab598'
TWILIO_ACCOUNT_SID: str = ""
TWILIO_AUTH_TOKEN: str = ""

# CORS Settings
ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "farmbot.yourdomain.com"]
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://farmbot.yourdomain.com"
]

# File Upload Settings
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
UPLOAD_DIR: str = "uploads"

# Logging Configuration
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: str = "logs/farmbot.log"

# Monitoring Settings
SENTRY_DSN: Optional[str] = None
ENABLE_METRICS: bool = True
METRICS_PORT: int = 9090

# Rate Limiting
RATE_LIMIT_PER_MINUTE: int = 60
RATE_LIMIT_BURST: int = 10

# Email Configuration
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
EMAILS_FROM_EMAIL: str = "noreply@farmbot.com"

# Cloud Storage (AWS S3)
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""
AWS_REGION: str = "ap-south-1"
S3_BUCKET_NAME: str = "farmbot-images"

# Performance Settings
WORKER_CONNECTIONS: int = 1000
WORKER_CLASS: str = "uvicorn.workers.UvicornWorker"
WORKERS: int = 4

# Feature Flags
ENABLE_VISION_AI: bool = True
ENABLE_LIVE_MARKET_DATA: bool = True
ENABLE_GOVERNMENT_SCHEMES: bool = True
ENABLE_WEATHER_SERVICE: bool = True
ENABLE_CACHING: bool = True

# Language Settings
DEFAULT_LANGUAGE: str = "hi"  # Hindi
SUPPORTED_LANGUAGES: List[str] = ["hi", "en", "bn", "te", "ta", "gu", "mr", "kn"]

# Market Data Settings
MARKET_DATA_CACHE_MINUTES: int = 5
PRICE_FORECAST_DAYS: int = 7
MAX_MARKETS_PER_COMMODITY: int = 10

# Vision AI Settings
VISION_AI_TIMEOUT: int = 30
IMAGE_ENHANCEMENT_ENABLED: bool = True
MAX_DIAGNOSIS_CONFIDENCE: float = 95.0

# Government Schemes Settings
SCHEMES_CACHE_HOURS: int = 24
SCHEMES_SCRAPING_ENABLED: bool = True

# Weather Settings
WEATHER_CACHE_MINUTES: int = 10
WEATHER_FORECAST_DAYS: int = 7

# Agent System Settings
ADK_APP_NAME: str = "farmbot_production_v2"
AGENT_TIMEOUT: int = 60
MAX_AGENT_RETRIES: int = 3

# Backup Settings
BACKUP_ENABLED: bool = True
BACKUP_INTERVAL_HOURS: int = 24
BACKUP_RETENTION_DAYS: int = 30
BACKUP_S3_BUCKET: str = "farmbot-backups"

# @validator("ALLOWED_HOSTS", pre=True)
def parse_hosts(cls, v):
    if isinstance(v, str):
        return [host.strip() for host in v.split(",")]
    return v

# @validator("ALLOWED_ORIGINS", pre=True)
def parse_origins(cls, v):
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    return v

# @validator("SUPPORTED_LANGUAGES", pre=True)
def parse_languages(cls, v):
    if isinstance(v, str):
        return [lang.strip() for lang in v.split(",")]
    return v

# @validator("ENVIRONMENT")
def validate_environment(cls, v):
    if v not in ["development", "staging", "production"]:
        raise ValueError("Environment must be development, staging, or production")
    return v

# @property
def is_development(self) -> bool:
    return self.ENVIRONMENT == "development"

# @property
def is_production(self) -> bool:
    return self.ENVIRONMENT == "production"

# @property
# def database_url_async(self) -> str:
#     """Get async database URL"""
#     return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

class Config:
    env_file = ".env"
    case_sensitive = True


# @lru_cache()
# def get_settings() -> Settings:
#     """Get cached settings instance"""
#     return Settings()


# # Global settings instance
# settings = get_settings()