from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
import httpx
from sqlmodel import Session, select
from ..models.database import Dialogue, DialogueCreate, ChatwootWebhook, DifyResponse
from ..database import get_db
from .. import tasks
from typing import Dict, Any
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

@router.post("/chatwoot-webhook")
async def chatwoot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    payload = await request.json()
    webhook_data = ChatwootWebhook.model_validate(payload)
    
    logger.info(f"Received webhook event: {webhook_data.event}")
    logger.debug(f"Webhook payload: {payload}")

    if webhook_data.event == "message_created":
        if webhook_data.sender_type == "agent_bot":
            return {"status": "skipped", "reason": "agent_bot message"}

        if webhook_data.message_type == "incoming" and webhook_data.status == "pending":
            try:
                dialogue_data = webhook_data.to_dialogue_create()
                dialogue = await get_or_create_dialogue(db, dialogue_data)

                # Get response from Dify via Celery task
                task = tasks.process_message_with_dify.delay(
                    message=webhook_data.content,
                    dify_conversation_id=dialogue.dify_conversation_id
                )
                task_result = task.get()  # This blocks until the task is complete
                
                # Convert dict to DifyResponse object
                dify_response_data = DifyResponse(**task_result)
                
                if dify_response_data.conversation_id and not dialogue.dify_conversation_id:
                    dialogue.dify_conversation_id = dify_response_data.conversation_id
                    db.commit()
                
                await chatwoot.send_message(
                    conversation_id=webhook_data.conversation_id,
                    message=dify_response_data.answer
                )
            except Exception as e:
                logger.error(f"Failed to process message with Dify: {e}")
                await chatwoot.send_message(
                    conversation_id=webhook_data.conversation_id,
                    message="Sorry, I'm having trouble processing your message right now."
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
                tasks.delete_dify_conversation,
                dialogue.dify_conversation_id
            )
            db.delete(dialogue)
            db.commit()
    
    return {"status": "success"} 