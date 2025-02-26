from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Body
import httpx
from sqlmodel import Session, select
from ..models.database import Dialogue, DialogueCreate, ChatwootWebhook, DifyResponse
from ..database import get_db
from .. import tasks
from typing import Dict, Any, List
from datetime import datetime
from .chatwoot import ChatwootHandler
import logging
from .. import config

logger = logging.getLogger(__name__)

router = APIRouter()
chatwoot = ChatwootHandler()


async def get_or_create_dialogue(db: Session, data: DialogueCreate) -> Dialogue:
    """
    Get existing dialogue or create a new one.
    Updates the dialogue if it exists with new data.
    """
    statement = select(Dialogue).where(
        Dialogue.chatwoot_conversation_id == data.chatwoot_conversation_id
    )
    dialogue = db.exec(statement).first()

    if dialogue:
        # Update existing dialogue with new data
        for field, value in data.dict(exclude_unset=True).items():
            setattr(dialogue, field, value)
        dialogue.updated_at = datetime.utcnow()
    else:
        # Create new dialogue
        dialogue = Dialogue(**data.dict())
        db.add(dialogue)

    db.commit()
    db.refresh(dialogue)
    return dialogue


@router.post("/send-chatwoot-message")
async def send_chatwoot_message(
    conversation_id: int,
    message: str,
    is_private: bool = False,
    db: Session = Depends(get_db),
):
    """
    Send a message to Chatwoot conversation.
    Can be used as a private note if is_private=True
    """
    try:
        # For private notes, we need to set both private=True and message_type="private"
        await chatwoot.send_message(
            conversation_id=conversation_id,
            message=message,
            private=is_private,
        )
        return {"status": "success", "message": "Message sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send message to Chatwoot: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to send message to Chatwoot"
        )


@router.post("/chatwoot-webhook")
async def chatwoot_webhook(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    print("Received Chatwoot webhook request")
    payload = await request.json()
    webhook_data = ChatwootWebhook.model_validate(payload)

    logger.info(f"Received webhook event: {webhook_data.event}")
    logger.debug(f"Webhook payload: {payload}")

    if webhook_data.event == "message_created":
        print(f"Webhook data: {webhook_data}")
        if webhook_data.sender_type == "agent_bot":
            logger.info(f"Skipping agent_bot message: {webhook_data.content}")
            return {"status": "skipped", "reason": "agent_bot message"}
        if webhook_data.message_type == "incoming" and webhook_data.status in [
            "pending",
            "open",
        ]:
            try:
                dialogue_data = webhook_data.to_dialogue_create()
                dialogue = await get_or_create_dialogue(db, dialogue_data)

                # Get response from Dify via Celery task
                task = tasks.process_message_with_dify.delay(
                    message=webhook_data.content,
                    dify_conversation_id=dialogue.dify_conversation_id,
                )
                task_result = task.get()  # This blocks until the task is complete

                # Convert dict to DifyResponse object
                dify_response_data = DifyResponse(**task_result)
                print(f"Dify response data: {dify_response_data}")

                if (
                    dify_response_data.conversation_id
                    and not dialogue.dify_conversation_id
                ):
                    dialogue.dify_conversation_id = dify_response_data.conversation_id
                    db.commit()

                await send_chatwoot_message(
                    conversation_id=webhook_data.conversation_id,
                    message=dify_response_data.answer,
                    is_private=False,
                    db=db,
                )
            except Exception as e:
                logger.error(f"Failed to process message with Dify: {e}")
                await send_chatwoot_message(
                    conversation_id=webhook_data.conversation_id,
                    message="Sorry, I'm having trouble processing your message right now.",
                    is_private=False,
                    db=db,
                )

    elif webhook_data.event == "conversation_created":
        if not webhook_data.conversation:
            return {"status": "skipped", "reason": "no conversation data"}

        dialogue_data = webhook_data.to_dialogue_create()
        dialogue = await get_or_create_dialogue(db, dialogue_data)
        return {"status": "success", "dialogue_id": dialogue.id}

    elif webhook_data.event == "conversation_updated":
        if not webhook_data.conversation:
            return {"status": "skipped", "reason": "no conversation data"}

        dialogue_data = webhook_data.to_dialogue_create()
        dialogue = await get_or_create_dialogue(db, dialogue_data)
        return {"status": "success", "dialogue_id": dialogue.id}

    elif webhook_data.event == "conversation_deleted":
        if not webhook_data.conversation:
            return {"status": "skipped", "reason": "no conversation data"}

        conversation_id = str(webhook_data.conversation.id)
        statement = select(Dialogue).where(
            Dialogue.chatwoot_conversation_id == conversation_id
        )
        dialogue = db.exec(statement).first()

        if dialogue and dialogue.dify_conversation_id:
            background_tasks.add_task(
                tasks.delete_dify_conversation, dialogue.dify_conversation_id
            )
            db.delete(dialogue)
            db.commit()

    return {"status": "success"}


@router.post("/update-labels/{conversation_id}")
async def update_labels(
    conversation_id: int, labels: List[str], db: Session = Depends(get_db)
):
    """
    Update labels for a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - labels: List of label strings to apply to the conversation (request body)
    """
    try:
        result = await chatwoot.add_labels(
            conversation_id=conversation_id, labels=labels
        )
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "labels": result,
        }
    except Exception as e:
        logger.error(f"Failed to update labels for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update labels: {str(e)}"
        )


@router.post("/update_custom_attributes/{conversation_id}")
async def update_custom_attributes(
    conversation_id: int,
    custom_attributes: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Update custom attributes for a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - custom_attributes: Dictionary of custom attributes to set (request body)

    Example request body:
    {"region": "Moscow"}
    """
    try:
        result = await chatwoot.update_custom_attributes(
            conversation_id=conversation_id, custom_attributes=custom_attributes
        )
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "custom_attributes": result,
        }
    except Exception as e:
        logger.error(
            f"Failed to update custom attributes for conversation {conversation_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update custom attributes: {str(e)}"
        )


@router.post("/toggle-priority/{conversation_id}")
async def toggle_conversation_priority(
    conversation_id: int,
    priority: str = Body(
        ...,
        embed=True,
        description="Priority level: 'urgent', 'high', 'medium', 'low', or None",
    ),
    db: Session = Depends(get_db),
):
    """
    Toggle the priority of a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - priority: Priority level to set (request body)

    Example request body:
        {
            "priority": "high"
        }
    """
    try:
        result = await chatwoot.toggle_priority(
            conversation_id=conversation_id, priority=priority
        )
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "priority": result,
        }
    except Exception as e:
        logger.error(
            f"Failed to toggle priority for conversation {conversation_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle priority: {str(e)}"
        )
