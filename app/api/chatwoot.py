import logging
from typing import Any, Dict, List, Optional

import httpx

from .. import config

logger = logging.getLogger(__name__)


class ChatwootHandler:
    def __init__(self, api_url: str | None = None, api_key: str | None = None, account_id: str | None = None):
        self.api_url = api_url or config.CHATWOOT_API_URL
        self.account_id = account_id or config.CHATWOOT_ACCOUNT_ID
        self.api_key = api_key or config.CHATWOOT_API_KEY
        self.headers = {
            "api_access_token": self.api_key,
            "Content-Type": "application/json",
        }
        # Base URLs
        self.account_url = f"{self.api_url}/accounts/{self.account_id}"
        self.conversations_url = f"{self.account_url}/conversations"

    async def send_message(
        self,
        conversation_id: int,
        message: str,
        private: bool = False,
        attachments: List[str] | None = None,
        content_attributes: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Send a message or private note to a conversation with rich content support"""
        url = f"{self.conversations_url}/{conversation_id}/messages"
        data = {
            "content": message,
            "message_type": "outgoing",
            "private": private,
            "content_attributes": content_attributes or {},
        }

        if attachments:
            data["attachments"] = [{"url": url} for url in attachments]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to send message to conversation {conversation_id}: {e}")
            raise

    async def update_conversation_status(
        self,
        conversation_id: int,
        status: str,
        priority: Optional[str] = None,
        snoozed_until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update conversation status and attributes
        Valid statuses: 'open', 'resolved', 'pending', 'snoozed'
        """
        url = f"{self.conversations_url}/{conversation_id}"
        data = {"status": status, "priority": priority, "snoozed_until": snoozed_until}
        data = {k: v for k, v in data.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Status update failed for conversation {conversation_id}:\n"
                f"URL: {url}\nStatus: {e.response.status_code}\n"
                f"Response: {e.response.text}\nPayload: {data}",
                exc_info=True,
            )
            raise

    async def add_labels(self, conversation_id: int, labels: List[str]) -> Dict[str, Any]:
        """Add labels to a conversation"""
        url = f"{self.conversations_url}/{conversation_id}/labels"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"labels": labels}, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add labels to conversation {conversation_id}: {e}")
            raise

    async def get_conversation_data(self, conversation_id: int) -> Dict[str, Any]:
        """Get conversation data including custom attributes and labels"""
        url = f"{self.conversations_url}/{conversation_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Get conversation failed for {conversation_id}:\n"
                f"URL: {url}\nStatus: {e.response.status_code}\n"
                f"Response: {e.response.text}",
                exc_info=True,
            )
            raise

    async def assign_conversation(self, conversation_id: int, assignee_id: int) -> Dict[str, Any]:
        """Assign a conversation to an agent."""
        url = f"{self.conversations_url}/{conversation_id}/assignments"
        data = {"assignee_id": assignee_id}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to assign conversation {conversation_id} to agent {assignee_id}: {e}")
            raise

    async def update_custom_attributes(self, conversation_id: int, custom_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Update custom attributes for a conversation"""
        custom_attrs_url = f"{self.conversations_url}/{conversation_id}/custom_attributes"

        try:
            async with httpx.AsyncClient() as client:
                # First get existing custom attributes from conversation endpoint
                get_response = await self.get_conversation_data(conversation_id)
                existing_attributes = get_response.get("custom_attributes", {})

                # Merge existing attributes with new ones
                merged_attributes = {**existing_attributes, **custom_attributes}
                payload = {"custom_attributes": merged_attributes}

                # Update with merged attributes
                response = await client.post(custom_attrs_url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update custom attributes for convo {conversation_id}: {e}")
            raise

    async def toggle_priority(self, conversation_id: int, priority: str) -> Dict[str, Any]:
        """Toggle the priority of a conversation
        Valid priorities: 'urgent', 'high', 'medium', 'low', None
        """
        url = f"{self.conversations_url}/{conversation_id}"
        data = {"priority": priority}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Priority update failed for conversation {conversation_id}:\n"
                f"URL: {url}\nStatus: {e.response.status_code}\n"
                f"Response: {e.response.text}\nPriority: {priority}",
                exc_info=True,
            )
            raise

    def send_message_sync(self, conversation_id: int, message: str, private: bool = False):
        """Synchronous version of send_message for use in Celery tasks"""
        import httpx

        url = f"{self.conversations_url}/{conversation_id}/messages"

        data = {
            "content": message,
            "message_type": "outgoing",
            "private": private,
        }

        with httpx.Client() as client:
            response = client.post(url, json=data, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()

    async def assign_team(self, conversation_id: int, team_id: int = 3) -> Dict[str, Any]:
        """Assign a conversation to a team.

        Args:
            conversation_id: The ID of the conversation to assign
            team_id: The ID of the team to assign to (defaults to 3)
        """
        url = f"{self.conversations_url}/{conversation_id}/assignments"
        data = {"team_id": team_id}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to assign conversation {conversation_id} to team {team_id}: {e}")
            raise
