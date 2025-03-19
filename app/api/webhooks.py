import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .. import tasks
from ..database import get_db
from ..models.database import ChatwootWebhook, Dialogue, DialogueCreate
from ..models.non_database import ConversationPriority, ConversationStatus
from .chatwoot import ChatwootHandler

logger = logging.getLogger(__name__)

router = APIRouter()
chatwoot = ChatwootHandler()

# Team management
team_cache: Dict[str, int] = {}
team_cache_lock = asyncio.Lock()
last_update_time = 0


async def get_or_create_dialogue(db: AsyncSession, data: DialogueCreate) -> Dialogue:
    """
    Get existing dialogue or create a new one.
    Updates the dialogue if it exists with new data.
    """
    statement = select(Dialogue).where(Dialogue.chatwoot_conversation_id == data.chatwoot_conversation_id)
    result = await db.execute(statement)
    dialogue = result.scalar_one_or_none()

    if dialogue:
        # Update existing dialogue with new data
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(dialogue, field, value)
        dialogue.updated_at = datetime.utcnow()
    else:
        # Create new dialogue
        dialogue = Dialogue(**data.model_dump())
        db.add(dialogue)

    await db.commit()
    await db.refresh(dialogue)
    return dialogue


@router.post("/send-chatwoot-message")
async def send_chatwoot_message(
    conversation_id: int,
    message: str,
    is_private: bool = False,
    db: AsyncSession = Depends(get_db),
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
        raise HTTPException(status_code=500, detail="Failed to send message to Chatwoot") from e


@router.post("/chatwoot-webhook")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    print("Received Chatwoot webhook request")
    payload = await request.json()
    webhook_data = ChatwootWebhook.model_validate(payload)

    logger.info(f"Received webhook event: {webhook_data.event}")
    logger.debug(f"Webhook payload: {payload}")

    if webhook_data.event == "message_created":
        print(f"Webhook data: {webhook_data}")
        if webhook_data.sender_type in ["agent_bot", "????"]:
            logger.info(f"Skipping agent_bot message: {webhook_data.content}")
            return {"status": "skipped", "reason": "agent_bot message"}
        if webhook_data.message_type == "incoming" and webhook_data.status == "pending":
            print(f"Processing message: {webhook_data}")
            try:
                dialogue_data = webhook_data.to_dialogue_create()
                dialogue = await get_or_create_dialogue(db, dialogue_data)

                # Just start the task and return immediately
                tasks.process_message_with_dify.apply_async(
                    args=[
                        webhook_data.content,
                        dialogue.dify_conversation_id,
                        dialogue.chatwoot_conversation_id,
                    ],
                    link=tasks.handle_dify_response.s(
                        conversation_id=webhook_data.conversation_id,
                        dialogue_id=dialogue.id,
                    ),
                    link_error=tasks.handle_dify_error.s(
                        conversation_id=webhook_data.conversation_id,
                    ),
                )

                return {"status": "processing"}

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
        statement = select(Dialogue).where(Dialogue.chatwoot_conversation_id == conversation_id)
        dialogue = await db.execute(statement)
        dialogue = dialogue.scalar_one_or_none()

        if dialogue and dialogue.dify_conversation_id:
            background_tasks.add_task(tasks.delete_dify_conversation, dialogue.dify_conversation_id)
            await db.delete(dialogue)
            await db.commit()

    return {"status": "success"}


@router.post("/update-labels/{conversation_id}")
async def update_labels(conversation_id: int, labels: List[str], db: AsyncSession = Depends(get_db)):
    """
    Update labels for a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - labels: List of label strings to apply to the conversation (request body)
    """
    try:
        result = await chatwoot.add_labels(conversation_id=conversation_id, labels=labels)
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "labels": result,
        }
    except Exception as e:
        logger.error(f"Failed to update labels for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update labels: {str(e)}") from e


@router.post("/update-custom-attributes/{conversation_id}")
async def update_custom_attributes(
    conversation_id: int,
    custom_attributes: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """
    Update custom attributes for a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - custom_attributes: Dictionary of custom attributes to set (request body)

    Example request body:
    {"region": "Moscow", "region_original_string": "Moscow"}
    """
    try:
        result = await chatwoot.patch_custom_attributes(
            conversation_id=conversation_id, custom_attributes=custom_attributes
        )
        logger.info(f"Updated custom attributes for conversation {conversation_id}: {result}")
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "custom_attributes": result,
        }
    except Exception as e:
        # Log the full exception details including traceback
        logger.exception(f"Failed to update custom attributes for conversation {conversation_id}:")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "conversation_id": conversation_id,
                "attempted_attributes": custom_attributes,
                "traceback": f"{type(e).__name__}: {str(e)}",
            },
        ) from e


@router.post("/toggle-priority/{conversation_id}")
async def toggle_conversation_priority(
    conversation_id: int,
    priority: ConversationPriority = Body(
        ...,
        embed=True,
        description="Priority level: 'urgent', 'high', 'medium', 'low', or null",
    ),
    db: AsyncSession = Depends(get_db),
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
        priority_value = priority.value
        logger.info(f"Attempting to set priority {priority_value} for conversation {conversation_id}")
        result = await chatwoot.toggle_priority(conversation_id=conversation_id, priority=str(priority_value))
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "priority": result,
        }
    except Exception as e:
        # Log the full exception details
        logger.exception(f"Detailed error when toggling priority for conversation {conversation_id}:")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "conversation_id": conversation_id, "attempted_priority": str(priority_value)},
        ) from e


@router.get("/conversations/dify/{dify_conversation_id}")
async def get_chatwoot_conversation_id(dify_conversation_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get Chatwoot conversation ID from Dify conversation ID
    """
    statement = select(Dialogue).where(Dialogue.dify_conversation_id == dify_conversation_id)
    dialogue = await db.execute(statement)
    dialogue = dialogue.scalar_one_or_none()

    if not dialogue:
        raise HTTPException(status_code=404, detail=f"No conversation found with Dify ID: {dify_conversation_id}")

    return {
        "chatwoot_conversation_id": dialogue.chatwoot_conversation_id,
        "status": dialogue.status,
        "assignee_id": dialogue.assignee_id,
    }


async def update_team_cache():
    """Update the team name to ID mapping cache."""
    global team_cache, last_update_time

    async with team_cache_lock:
        try:
            teams = await chatwoot.get_teams()

            # Create case-insensitive mappings from name to ID
            new_cache = {team["name"].lower(): team["id"] for team in teams}

            # Update the cache
            team_cache = new_cache
            last_update_time = datetime.utcnow().timestamp()

            logger.info(f"Updated team cache with {len(team_cache)} teams")
            return team_cache
        except Exception as e:
            logger.error(f"Failed to update team cache: {e}", exc_info=True)
            raise


async def get_team_id(team_name: str) -> Optional[int]:
    """Get team ID from name, updating cache if necessary.

    Args:
        team_name: The name of the team to look up

    Returns:
        The team ID or None if not found
    """
    if not team_cache or (datetime.utcnow().timestamp() - last_update_time) > 24 * 3600:  # Cache for 24 hour
        await update_team_cache()

    return team_cache.get(team_name.lower())


@router.post("/refresh-teams")
async def refresh_teams_cache():
    """Manually refresh the team cache."""
    try:
        teams = await update_team_cache()
        return {"status": "success", "teams": len(teams)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh teams: {str(e)}") from e


@router.post("/assign-team/{conversation_id}")
async def assign_conversation_to_team(
    conversation_id: int,
    team: str = Body(
        ...,
        embed=True,
        description="Team name to assign the conversation to",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a Chatwoot conversation to a team

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - team: Team name to assign (request body)

    Example request body:
        {
            "team": "Support"
        }
    """
    try:
        # Log the attempt
        logger.info(f"Attempting to assign conversation {conversation_id} to team {team}")

        # Get team_id from name
        team_id = await get_team_id(team)

        if team_id is None:
            # Try to refresh the cache and try again
            await update_team_cache()
            team_id = await get_team_id(team)

            if team_id is None:
                raise HTTPException(
                    status_code=404, detail=f"Team '{team}' not found. Available teams: {list(team_cache.keys())}"
                )

        # Assign the conversation to the team
        result = await chatwoot.assign_team(conversation_id=conversation_id, team_id=team_id)

        # Log successful result
        logger.info(f"Successfully assigned conversation {conversation_id} to team {team} (ID: {team_id})")

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "team": team,
            "team_id": team_id,
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        # Log the full exception details
        logger.exception(f"Detailed error when assigning team for conversation {conversation_id}:")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "conversation_id": conversation_id,
                "attempted_team": team,
                "available_teams": list(team_cache.keys()),
            },
        ) from e


@router.post("/toggle-status/{conversation_id}")
async def toggle_conversation_status(
    conversation_id: int,
    status: ConversationStatus = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle the status of a Chatwoot conversation

    Parameters:
    - conversation_id: The ID of the conversation to update (path parameter)
    - status: Status to set (request body)

    Example request body:
        {
            "status": "open"
        }
    """
    try:
        result = await chatwoot.toggle_status(conversation_id=conversation_id, status=status.value)
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "result": result,
        }
    except Exception as e:
        logger.exception(f"Failed to toggle status for conversation {conversation_id}:")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "conversation_id": conversation_id},
        ) from e


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events manager"""
    # Startup
    try:
        await update_team_cache()
        logger.info(f"Initialized team cache with {len(team_cache)} teams")
    except Exception as e:
        logger.error(f"Failed to initialize team cache: {e}", exc_info=True)
    yield
    # Shutdown
    pass
