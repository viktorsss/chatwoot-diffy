import logging
from typing import Any, Dict, Optional

import httpx
from celery import Celery
from dotenv import load_dotenv

from . import config
from .api.chatwoot import ChatwootHandler
from .config import SKIPPED_MESSAGE
from .database import SessionLocal
from .models.database import Dialogue, DifyResponse

load_dotenv()

# Use timeout constants from config
HTTPX_TIMEOUT = httpx.Timeout(
    connect=config.HTTPX_CONNECT_TIMEOUT,
    read=config.HTTPX_READ_TIMEOUT,
    write=config.HTTPX_WRITE_TIMEOUT,
    pool=config.HTTPX_POOL_TIMEOUT,
)

# Use LOG_LEVEL from config instead of directly from environment
LOG_LEVEL = config.LOG_LEVEL

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
    message: str,
    dify_conversation_id: Optional[str] = None,
    chatwoot_conversation_id: Optional[str] = None,
    conversation_status: Optional[str] = None,
    message_type: Optional[str] = None,  # `incoming` and `outgoing`
) -> Dict[str, Any]:
    """
    Process a message with Dify and return the response as a dictionary.
    """
    if message.startswith(SKIPPED_MESSAGE):
        return {"status": "skipped", "reason": "agent_bot message"}
    url = f"{config.DIFY_API_URL}/chat-messages"
    headers = {"Authorization": f"Bearer {config.DIFY_API_KEY}", "Content-Type": "application/json"}

    # https://github.com/langgenius/dify/issues/11140 IMPORTANT : `inputs` are cached for conversation
    data = {
        "query": message,
        "inputs": {
            "chatwoot_conversation_id": chatwoot_conversation_id,
            "conversation_status": conversation_status,
            "message_direction": message_type,
        },
        "response_mode": config.DIFY_RESPONSE_MODE,
        "conversation_id": dify_conversation_id,
        "user": "user",
    }

    try:
        with httpx.Client(timeout=HTTPX_TIMEOUT) as client:
            response = client.post(url, json=data, headers=headers)
            # Store response content before raising exception
            if response.status_code >= 400:
                error_content = response.text
                logger.error(f"Dify API error response: {error_content}")
            response.raise_for_status()
            result = response.json()
            return result
    except Exception as e:
        logger.critical(f"Critical error processing message with Dify: {e}", exc_info=True)
        logger.error(f"Error processing message with Dify: {e}", exc_info=True)
        logger.warning(f"Warning - Dify conversation ID: {dify_conversation_id}")
        logger.warning(f"Warning - Chatwoot conversation ID: {chatwoot_conversation_id}")
        # If it's an HTTP error, try to extract and log the response content
        if isinstance(e, httpx.HTTPStatusError) and hasattr(e, "response"):
            logger.error(f"Response content: {e.response.text}")
        raise e from e


@celery.task(name="app.tasks.handle_dify_response")
def handle_dify_response(dify_result: Dict[str, Any], conversation_id: int, dialogue_id: int):
    """Handle the response from Dify"""

    chatwoot = ChatwootHandler()

    # Use context manager to ensure proper session management
    with SessionLocal() as db:
        try:
            dify_response_data = DifyResponse(**dify_result)

            # Update dialogue if needed
            if dify_response_data.conversation_id:
                dialogue = db.get(Dialogue, dialogue_id)
                if dialogue and not dialogue.dify_conversation_id:
                    dialogue.dify_conversation_id = dify_response_data.conversation_id
                    db.commit()

            # Send message back to Chatwoot. Sync is okay because we use separate instance of ChatwootHandler
            chatwoot.send_message_sync(
                conversation_id=conversation_id,
                message=dify_response_data.answer,
                private=False,
            )
        except Exception as e:
            logger.error(f"Error handling Dify response: {str(e)}", exc_info=True)
            # Re-raise to ensure Celery knows this task failed
            raise


@celery.task(name="app.tasks.handle_dify_error")
def handle_dify_error(request: Dict[str, Any], exc: Exception, traceback: str, conversation_id: int):
    """Handle any errors from the Dify task"""
    from .api.chatwoot import ChatwootHandler

    logger.error(f"Dify task failed for conversation {conversation_id}: {exc}")
    logger.debug(f"Failed request: {request}")
    logger.debug(f"Traceback: {traceback}")

    # Send message back to Chatwoot. Sync is okay because we use separate instance of ChatwootHandler
    chatwoot = ChatwootHandler()
    chatwoot.send_message_sync(
        conversation_id=conversation_id,
        message="Sorry, I'm having trouble processing your message right now.",
        private=False,
    )


@celery.task(name="app.tasks.delete_dify_conversation")
def delete_dify_conversation(dify_conversation_id: str):
    """Delete a conversation from Dify when it's deleted in Chatwoot"""
    logger.info(f"Deleting Dify conversation: {dify_conversation_id}")

    url = f"{config.DIFY_API_URL}/conversations/{dify_conversation_id}"
    headers = {"Authorization": f"Bearer {config.DIFY_API_KEY}", "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=HTTPX_TIMEOUT) as client:
            response = client.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Successfully deleted Dify conversation: {dify_conversation_id}")
            return {"status": "success", "conversation_id": dify_conversation_id}
    except Exception as e:
        logger.error(f"Failed to delete Dify conversation {dify_conversation_id}: {e}", exc_info=True)
        raise e from e
