from typing import Any, Dict, Optional

import httpx
from celery import Celery

from . import config

REDIS_BROKER = config.REDIS_BROKER
REDIS_BACKEND = config.REDIS_BACKEND

celery = Celery("celery_worker", broker=REDIS_BROKER, backend=REDIS_BACKEND, broker_connection_retry_on_startup=True)


@celery.task
def process_message_with_dify(message: str, dify_conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a message with Dify and return the response as a dictionary.
    """
    url = f"{config.DIFY_API_URL}/chat-messages"
    headers = {"Authorization": f"Bearer {config.DIFY_API_KEY}", "Content-Type": "application/json"}

    data = {
        "query": message,
        "inputs": {},
        "response_mode": config.DIFY_RESPONSE_MODE,
        "conversation_id": dify_conversation_id,
        "user": "user",
    }

    try:
        response = httpx.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        return {
            "event": result.get("event"),
            "task_id": result.get("task_id"),
            "id": result.get("id"),
            "message_id": result.get("message_id"),
            "conversation_id": result.get("conversation_id"),
            "mode": result.get("mode"),
            "answer": result.get("answer", "AI assistant is currently unavailable."),
            "metadata": result.get("metadata"),
            "created_at": result.get("created_at"),
        }
    except Exception:
        return {
            "answer": (
                "I apologize, but I'm temporarily unavailable. "
                "Please try again later or wait for a human operator to respond."
            )
        }
