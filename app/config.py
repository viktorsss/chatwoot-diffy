import os
from typing import List

# Core application settings
DEBUG = os.getenv("DEBUG", "False")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Database configuration
DB_HOST = "localhost" if DEBUG == "True" else os.getenv("DB_HOST", "db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_PORT = "5433" if DEBUG == "True" else "5432"
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwoot_dify")

# Connection strings
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6380")
REDIS_BROKER = os.getenv("REDIS_BROKER", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_BROKER)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_BACKEND)
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "300"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240"))
CELERY_TASK_MAX_TASKS_PER_CHILD = int(os.getenv("CELERY_TASK_MAX_TASKS_PER_CHILD", "100"))
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))

# Dify.ai configuration
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_RESPONSE_MODE = os.getenv("DIFY_RESPONSE_MODE", "blocking")
DIFY_TEMPERATURE = float(os.getenv("DIFY_TEMPERATURE", "0.7"))
DIFY_MAX_TOKENS = int(os.getenv("DIFY_MAX_TOKENS", "2000"))

# Chatwoot configuration
CHATWOOT_API_URL = os.getenv("CHATWOOT_API_URL", "https://app.chatwoot.com/api/v1")
CHATWOOT_API_KEY = os.getenv("CHATWOOT_API_KEY", "")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
ALLOWED_CONVERSATION_STATUSES = os.getenv("ALLOWED_CONVERSATION_STATUSES", "open,pending").split(",")

# OpenTelemetry configuration
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "chatwoot-dify")
OTEL_EXPORTER_OTLP_PROTOCOL = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
OTEL_PYTHON_EXCLUDED_URLS = os.getenv("OTEL_PYTHON_EXCLUDED_URLS", "healthcheck,metrics")

# SQLAlchemy engine configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "True").lower() in ("true", "1", "t")

# Testing configuration
TEST_CONVERSATION_ID = os.getenv("TEST_CONVERSATION_ID", "20")

# HTTPX timeout configuration
HTTPX_CONNECT_TIMEOUT = float(os.getenv("HTTPX_CONNECT_TIMEOUT", "30.0"))
HTTPX_READ_TIMEOUT = float(os.getenv("HTTPX_READ_TIMEOUT", "120.0"))
HTTPX_WRITE_TIMEOUT = float(os.getenv("HTTPX_WRITE_TIMEOUT", "30.0"))
HTTPX_POOL_TIMEOUT = float(os.getenv("HTTPX_POOL_TIMEOUT", "30.0"))

# Sentry configuration
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
SENTRY_LOG_LEVEL = os.getenv("SENTRY_LOG_LEVEL", "WARNING")
SENTRY_ATTACH_STACKTRACE = os.getenv("SENTRY_ATTACH_STACKTRACE", "True").lower() in ("true", "1", "t")
SENTRY_SEND_DEFAULT_PII = os.getenv("SENTRY_SEND_DEFAULT_PII", "False").lower() in ("true", "1", "t")

# some hardcoded string

BOT_ERROR_MESSAGE = "Ой! Наш бот сломался, но ваш диалог переведён к операторам. Не переживайте, с вами свяжутся!"


def valid_statuses() -> List[str]:
    valid = ["open", "pending", "resolved", "snoozed", "closed"]
    return [status for status in ALLOWED_CONVERSATION_STATUSES if status in valid]
