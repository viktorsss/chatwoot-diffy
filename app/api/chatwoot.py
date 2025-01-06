import httpx
from typing import Optional, Dict, Any
from .. import config
import logging

logger = logging.getLogger(__name__)

class ChatwootHandler:
    def __init__(self, api_url: str = None, api_key: str = None, account_id: str = None):
        self.api_url = api_url or config.CHATWOOT_API_URL
        self.account_id = account_id or config.CHATWOOT_ACCOUNT_ID
        self.api_key = api_key or config.CHATWOOT_API_KEY
        self.headers = {
            "api_access_token": self.api_key,
            "Content-Type": "application/json"
        }

    async def assign_conversation(self, conversation_id: int, assignee_id: int) -> Dict[str, Any]:
        """Assign a conversation to an agent."""
        url = f"{self.api_url}/accounts/{self.account_id}/conversations/{conversation_id}/assignments"
        data = {"assignee_id": assignee_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to assign conversation {conversation_id} to agent {assignee_id}: {e}")
            raise

    async def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """Get conversation details."""
        url = f"{self.api_url}/conversations/{conversation_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def send_message(self, conversation_id: int, message: str) -> Dict[str, Any]:
        """Send a message to a conversation."""
        url = f"{self.api_url}/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        data = {
            "content": message,
            "message_type": "outgoing"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json() 