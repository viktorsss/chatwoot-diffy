import logging
import os
from typing import Any, Dict, Optional

import httpx
from celery import Celery
from dotenv import load_dotenv

from . import config
from .api.chatwoot import ChatwootHandler
from .database import SessionLocal
from .models.database import Dialogue, DifyResponse

load_dotenv()

# Add timeout constants with more generous values
HTTPX_TIMEOUT = httpx.Timeout(
    connect=30.0,  # connection timeout
    read=120.0,  # read timeout - increased significantly for LLM responses
    write=30.0,  # write timeout
    pool=30.0,  # pool timeout
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


REDIS_BROKER = config.REDIS_BROKER
REDIS_BACKEND = config.REDIS_BACKEND

# Configure root logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,  # Override any existing configuration
)

# Ensure celery logging is properly configured
celery_logger = logging.getLogger("celery")
celery_logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

# Configure our app logger
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

# Ensure logs are propagated up
logger.propagate = True

celery = Celery("tasks")
celery.config_from_object(config, namespace="CELERY")


def make_dify_request(url: str, data: dict, headers: dict) -> dict:
    """Make a request to Dify API with retry logic"""
    with httpx.Client(timeout=HTTPX_TIMEOUT) as client:
        response = client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()


@celery.task
def process_message_with_dify(
    message: str, dify_conversation_id: Optional[str] = None, chatwoot_conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a message with Dify and return the response as a dictionary.
    """

    url = f"{config.DIFY_API_URL}/chat-messages"
    headers = {"Authorization": f"Bearer {config.DIFY_API_KEY}", "Content-Type": "application/json"}

    data = {
        "query": message,
        "inputs": {"chatwoot_conversation_id": chatwoot_conversation_id},
        "response_mode": config.DIFY_RESPONSE_MODE,
        "conversation_id": dify_conversation_id,
        "user": "user",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result
    except Exception as e:
        logger.critical(f"Critical error processing message with Dify: {e}", exc_info=True)
        logger.error(f"Error processing message with Dify: {e}", exc_info=True)
        logger.warning(f"Warning - Dify conversation ID: {dify_conversation_id}")
        logger.warning(f"Info - Chatwoot conversation ID: {chatwoot_conversation_id}")
        return {
            "answer": (
                "I apologize, but I'm temporarily unavailable. "
                "Please try again later or wait for a human operator to respond."
            )
        }


@celery.task(name="app.tasks.handle_dify_response")
def handle_dify_response(dify_result: Dict[str, Any], conversation_id: int, dialogue_id: int):
    """Handle the response from Dify"""

    chatwoot = ChatwootHandler()
    db = SessionLocal()

    try:
        dify_response_data = DifyResponse(**dify_result)

        # Update dialogue if needed
        if dify_response_data.conversation_id:
            dialogue = db.get(Dialogue, dialogue_id)
            if dialogue and not dialogue.dify_conversation_id:
                dialogue.dify_conversation_id = dify_response_data.conversation_id
                db.commit()

        # Send message back to Chatwoot
        chatwoot.send_message_sync(
            conversation_id=conversation_id,
            message=dify_response_data.answer,
            private=False,
        )
    finally:
        db.close()


@celery.task(name="app.tasks.handle_dify_error")
def handle_dify_error(request: Dict[str, Any], exc: Exception, traceback: str, conversation_id: int):
    """Handle any errors from the Dify task"""
    from .api.chatwoot import ChatwootHandler

    logger.error(f"Dify task failed for conversation {conversation_id}: {exc}")
    logger.debug(f"Failed request: {request}")
    logger.debug(f"Traceback: {traceback}")

    chatwoot = ChatwootHandler()
    chatwoot.send_message_sync(
        conversation_id=conversation_id,
        message="Sorry, I'm having trouble processing your message right now.",
        private=False,
    )
