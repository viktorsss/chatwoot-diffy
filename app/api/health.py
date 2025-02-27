import asyncio
import logging
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..api.chatwoot import ChatwootHandler
from ..config import DIFY_API_URL
from ..database import get_db
from ..models.database import Dialogue

router = APIRouter()
logger = logging.getLogger(__name__)

chatwoot = ChatwootHandler()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check of the system.
    Checks database, Chatwoot API, and Dify API connections.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "services": {
            "database": {"status": "unknown"},
            "chatwoot_api": {"status": "unknown"},
            "dify_api": {"status": "unknown"},
        },
        "details": {},
    }

    # Check database connection
    try:
        # Try to execute a simple query
        test_query = select(Dialogue).limit(1)
        db.exec(test_query)
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")

    # Check Chatwoot API
    try:
        teams = await chatwoot.get_teams()
        health_status["services"]["chatwoot_api"] = {
            "status": "healthy",
            "teams_available": len(teams),
        }
    except Exception as e:
        health_status["services"]["chatwoot_api"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"Chatwoot API health check failed: {e}")

    # Check Dify API connectivity
    # We'll just check if the URL is reachable, not actually making API calls
    try:
        async with asyncio.timeout(5):
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{DIFY_API_URL}/health-check", follow_redirects=True)
                if response.status_code < 500:  # Allow 4xx errors as they may require auth
                    health_status["services"]["dify_api"] = {"status": "healthy"}
                else:
                    health_status["services"]["dify_api"] = {
                        "status": "unhealthy",
                        "http_status": response.status_code,
                    }
                    health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["dify_api"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"Dify API health check failed: {e}")

    # If any service is unhealthy, the overall status is degraded
    if any(service["status"] == "unhealthy" for service in health_status["services"].values()):
        health_status["status"] = "degraded"

    # Add response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return health_status


@router.post("/test-conversation")
async def create_test_conversation(db: Session = Depends(get_db)):
    """
    Creates a test conversation in Chatwoot for testing purposes.
    This endpoint is for development and testing only.
    """
    try:
        # Create a test conversation through Chatwoot API
        # This would be a real conversation that the system can interact with
        # Implementation will depend on the available Chatwoot API endpoints

        # Example implementation - this would need to be adjusted based on
        # available Chatwoot endpoints for creating conversations
        test_message = f"Test message created at {time.time()} Acknowledge receiving by saying `I see a test message`"

        # For now, we'll just try to get some existing conversations to verify API works
        conversations = await chatwoot.get_conversation_list()

        if conversations and len(conversations) > 0:
            # If conversations exist, use the first one for testing
            test_conversation_id = conversations[0].get("id")

            # Send a test message to this conversation
            result = await chatwoot.send_message(
                conversation_id=test_conversation_id,
                message=f"Health check: {test_message}",
                private=True,  # Use private so it doesn't disturb real users
            )

            return {
                "status": "success",
                "conversation_id": test_conversation_id,
                "message": (
                    "Test message sent to existing conversation Acknowledge receiving by saying `I see a test message`"
                ),
                "result": result,
            }
        else:
            # In a real implementation, we would create a new conversation here
            return {
                "status": "warning",
                "message": "No existing conversations found to test with",
                "note": "Creating new conversations requires additional Chatwoot API endpoints",
            }
    except Exception as e:
        logger.error(f"Failed to create test conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create test conversation: {str(e)}") from e
