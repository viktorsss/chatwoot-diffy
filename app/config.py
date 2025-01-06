import os
from typing import List

DEBUG = os.getenv("DEBUG", "False")
DB_HOST = "localhost" if DEBUG == "True" else os.getenv("DB_HOST", "db")
POSTGRES_USER=os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", "password")
DB_PORT = "5433" if DEBUG == "True" else "5432"
POSTGRES_DB=os.getenv("POSTGRES_DB", "chatwoot_dify")

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

def valid_statuses() -> List[str]:
    valid = ["open", "pending", "resolved", "snoozed", "closed"]
    return [status for status in ALLOWED_CONVERSATION_STATUSES if status in valid] 