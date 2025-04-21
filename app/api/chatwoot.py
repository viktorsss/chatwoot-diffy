import logging
from typing import Any, Dict, List, Optional

import httpx

from .. import config

logger = logging.getLogger(__name__)


class ChatwootHandler:
    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        account_id: str | None = None,
        admin_api_key: str | None = None,
    ):
        self.api_url = api_url or config.CHATWOOT_API_URL
        self.account_id = account_id or config.CHATWOOT_ACCOUNT_ID
        self.api_key = api_key or config.CHATWOOT_API_KEY
        self.admin_api_key = admin_api_key or config.CHATWOOT_ADMIN_API_KEY
        self.headers = {
            "api_access_token": self.api_key,
            "Content-Type": "application/json",
        }
        self.admin_headers = {
            "api_access_token": self.admin_api_key,
            "Content-Type": "application/json",
        }
        # Base URLs
        self.account_url = f"{self.api_url}/accounts/{self.account_id}"
        self.conversations_url = f"{self.account_url}/conversations"

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
                response = await client.get(url, headers=self.admin_headers)
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
        """Update custom attributes for a conversation using the provided account_id and conversation_id."""
        custom_attrs_url = f"{self.conversations_url}/{conversation_id}/custom_attributes"

        try:
            async with httpx.AsyncClient() as client:
                payload = {"custom_attributes": custom_attributes}

                # Use POST to update attributes
                response = await client.post(custom_attrs_url, json=payload, headers=self.headers)
                response.raise_for_status()
                if response.content and len(response.content.strip()) > 0:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.warning(f"Failed to parse JSON response: {json_err}")
                        return {}
                return {}
        except Exception as e:
            logger.error(f"Failed to update custom attributes for conversation {conversation_id}: {e}")
            raise

    async def toggle_priority(self, conversation_id: int, priority: str) -> Dict[str, Any]:
        """Toggle the priority of a conversation
        Valid priorities: 'urgent', 'high', 'medium', 'low', None
        """
        url = f"{self.conversations_url}/{conversation_id}/toggle_priority"
        data = {"priority": priority}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                if response.content and len(response.content.strip()) > 0:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.warning(f"Failed to parse JSON response: {json_err}")
                        return {}
                return {}
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Priority update failed for conversation {conversation_id}:\n"
                f"URL: {url}\nStatus: {e.response.status_code}\n"
                f"Response: {e.response.text}\nPriority: {priority}",
                exc_info=True,
            )
            raise

    async def assign_team(
        self, conversation_id: int, team_id: int = 0, team_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign a conversation to a team.

        Args:
            conversation_id: The ID of the conversation to assign
            team_id: The ID of the team to assign to
            team_name: The name of the team to assign to (will be looked up if provided)
        """
        url = f"{self.conversations_url}/{conversation_id}/assignments"

        # Use team name to get team_id if provided
        if team_name and not team_id:
            teams = await self.get_teams()
            team_map = {team["name"].lower(): team["id"] for team in teams}
            team_id = team_map.get(team_name.lower(), 0)

        data = {"team_id": team_id}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to assign conversation {conversation_id} to team {team_id or team_name}: {e}")
            raise

    async def create_custom_attribute_definition(
        self,
        display_name: str,
        attribute_key: str,
        attribute_values: List[str],
        description: str = "",
        attribute_model: int = 0,
    ) -> Dict[str, Any]:
        """Create a new custom attribute definition for conversations or contacts.

        Args:
            display_name: The display name for the attribute
            attribute_key: Unique key for the attribute
            attribute_values: List of possible values for the list-type attribute
            description: Optional description of the attribute
            attribute_model: 0 for conversation attribute, 1 for contact attribute
        """
        url = f"{self.account_url}/custom_attribute_definitions"
        data = {
            "attribute_display_name": display_name,
            "attribute_display_type": 6,  # 6 represents list type
            "attribute_description": description,
            "attribute_key": attribute_key,
            "attribute_values": attribute_values,
            "attribute_model": attribute_model,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to create custom attribute definition: {e}")
            raise

    async def toggle_status(self, conversation_id: int, status: str) -> Dict[str, Any]:
        """Toggle conversation status
        Valid statuses: 'open', 'resolved', 'pending', 'snoozed'
        """
        url = f"{self.conversations_url}/{conversation_id}/toggle_status"
        data = {"status": status}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
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

    def toggle_status_sync(self, conversation_id: int, status: str) -> Dict[str, Any]:
        """Toggle conversation status synchronously
        Valid statuses: 'open', 'resolved', 'pending', 'snoozed'
        """
        url = f"{self.conversations_url}/{conversation_id}/toggle_status"
        data = {"status": status}

        try:
            with httpx.Client() as client:
                response = client.post(url, json=data, headers=self.headers)
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

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all teams from the Chatwoot account.

        Returns:
            List of team objects with properties like id, name, description, etc.
        """
        url = f"{self.account_url}/teams"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.admin_headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to fetch teams:\nURL: {url}\nStatus: {e.response.status_code}\nResponse: {e.response.text}",
                exc_info=True,
            )
            logger.warning("Resroting to using hardcoded teams")
            return [
                {
                    "id": 3,
                    "name": "срочная служба",
                    "description": "",
                    "allow_auto_assign": True,
                    "private": False,
                    "account_id": 1,
                    "is_member": True,
                },
                {
                    "id": 4,
                    "name": "консультанты",
                    "description": "",
                    "allow_auto_assign": True,
                    "private": False,
                    "account_id": 1,
                    "is_member": True,
                },
                {
                    "id": 5,
                    "name": "мобилизация",
                    "description": "",
                    "allow_auto_assign": True,
                    "private": False,
                    "account_id": 1,
                    "is_member": True,
                },
                {
                    "id": 6,
                    "name": "дезертиры",
                    "description": "",
                    "allow_auto_assign": True,
                    "private": False,
                    "account_id": 1,
                    "is_member": True,
                },
            ]

    async def get_conversation_list(self, status: str = "all", assignee_type: str = "all") -> List[Dict[str, Any]]:
        """Get a list of conversations based on filters.

        Args:
            status: Filter by conversation status (all, open, resolved, pending)
            assignee_type: Filter by assignee (all, me, unassigned)

        Returns:
            List of conversation objects
        """
        url = f"{self.conversations_url}?status={status}&assignee_type={assignee_type}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get conversation list: {e}")
            raise
