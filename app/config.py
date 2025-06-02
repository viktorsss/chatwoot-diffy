import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

# Core application settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatdify")

# Connection strings
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6380")
REDIS_BROKER = os.getenv("REDIS_BROKER", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

# Celery configuration - using modern naming conventions for Celery 5.x+
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_BROKER)  # Keep for backwards compatibility
# Note: CELERY_RESULT_BACKEND is deprecated, now using result_backend below

# New Celery settings (lowercase without CELERY_ prefix for use with namespace="CELERY")
# These are the modern Celery 5.x+ configuration names
broker_url = os.getenv("CELERY_BROKER_URL", REDIS_BROKER)
result_backend = os.getenv("CELERY_RESULT_BACKEND", REDIS_BACKEND)
worker_concurrency = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
task_time_limit = int(os.getenv("CELERY_TASK_TIME_LIMIT", "300"))
task_soft_time_limit = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240"))
task_max_retries = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))
worker_max_tasks_per_child = int(os.getenv("CELERY_TASK_MAX_TASKS_PER_CHILD", "100"))
worker_prefetch_multiplier = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))

# Celery 6.0 compatibility settings
broker_connection_retry_on_startup = True  # Retain current behavior for connection retries

# Custom settings for our application
CELERY_RETRY_COUNTDOWN = int(os.getenv("CELERY_RETRY_COUNTDOWN", "5"))

# Dify.ai configuration
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_RESPONSE_MODE = os.getenv("DIFY_RESPONSE_MODE", "blocking")
DIFY_TEMPERATURE = float(os.getenv("DIFY_TEMPERATURE", "0.7"))
DIFY_MAX_TOKENS = int(os.getenv("DIFY_MAX_TOKENS", "2000"))
# Constants potentially used for polling/checking Dify conversation status (from tests)
DIFY_CHECK_WAIT_TIME = int(os.getenv("DIFY_CHECK_WAIT_TIME", "15"))
DIFY_CHECK_POLL_INTERVAL = int(os.getenv("DIFY_CHECK_POLL_INTERVAL", "2"))

# Chatwoot configuration
CHATWOOT_API_URL = os.getenv("CHATWOOT_API_URL", "https://app.chatwoot.com/api/v1")
CHATWOOT_API_KEY = os.getenv("CHATWOOT_API_KEY", "")
CHATWOOT_ADMIN_API_KEY = os.getenv("CHATWOOT_ADMIN_API_KEY", "")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
ALLOWED_CONVERSATION_STATUSES = os.getenv("ALLOWED_CONVERSATION_STATUSES", "open,pending").split(",")

# Team cache configuration - disabled by default for better API reliability
ENABLE_TEAM_CACHE = os.getenv("ENABLE_TEAM_CACHE", "False").lower() in ("true", "1", "t")
TEAM_CACHE_TTL_HOURS = int(os.getenv("TEAM_CACHE_TTL_HOURS", "24"))  # Cache for 24 hours by default

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
SENTRY_ATTACH_STACKTRACE = os.getenv("SENTRY_ATTACH_STACKTRACE", "True").lower() in (
    "true",
    "1",
    "t",
)
SENTRY_SEND_DEFAULT_PII = os.getenv("SENTRY_SEND_DEFAULT_PII", "False").lower() in (
    "true",
    "1",
    "t",
)

# some hardcoded string

BOT_ERROR_MESSAGE_INTERNAL = os.getenv(
    "BOT_ERROR_MESSAGE_INTERNAL",
    "Bot unexpectedly broke down, conversation moved to open status",
)

BOT_CONVERSATION_OPENED_MESSAGE_EXTERNAL = os.getenv(
    "BOT_CONVERSATION_OPENED_MESSAGE_EXTERNAL",
    "Your conversation has been transferred to operators. Don't worry, they will contact you!",
)


def valid_statuses() -> List[str]:
    valid = ["open", "pending", "resolved", "snoozed", "closed"]
    return [status for status in ALLOWED_CONVERSATION_STATUSES if status in valid]
