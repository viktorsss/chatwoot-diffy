import os
from typing import List

DEBUG = os.getenv("DEBUG", "False")
DB_HOST = "localhost" if DEBUG == "True" else os.getenv("DB_HOST", "db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_PORT = "5433" if DEBUG == "True" else "5432"
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwoot_dify")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
REDIS_BROKER = os.getenv("REDIS_BROKER", "redis://redis:6380")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "redis://redis:6380")

DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_RESPONSE_MODE = "blocking"
DIFY_TEMPERATURE = 0.7
DIFY_MAX_TOKENS = 2000

CHATWOOT_API_URL = os.getenv("CHATWOOT_API_URL", "https://app.chatwoot.com/api/v1")
CHATWOOT_API_KEY = os.getenv("CHATWOOT_API_KEY", "")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
ALLOWED_CONVERSATION_STATUSES = ["open", "pending"]

# SQLAlchemy engine configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "True").lower() in ("true", "1", "t")


def valid_statuses() -> List[str]:
    valid = ["open", "pending", "resolved", "snoozed", "closed"]
    return [status for status in ALLOWED_CONVERSATION_STATUSES if status in valid]
