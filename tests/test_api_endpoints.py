import os

import aiohttp
import pytest
from dotenv import load_dotenv

load_dotenv()

# API base URL - get from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def http_client():
    async with aiohttp.ClientSession() as client:
        yield client


async def test_health_endpoint(http_client):
    """Test the health check endpoint"""
    async with http_client.get(f"{API_BASE_URL}/health") as response:
        assert response.status == 200
        data = await response.json()
        assert "status" in data
        assert "services" in data
        assert "database" in data["services"]
        assert "chatwoot_api" in data["services"]
        assert "dify_api" in data["services"]


async def test_webhook_endpoint(http_client):
    """Test the webhook endpoint with a mock webhook event"""
    # This is a minimal webhook payload that should be accepted
    webhook_payload = {
        "event": "message_created",
        "message_type": "incoming",
        "content": (
            "Test message from automated test, intended to mimic a user. "
            "Acknowledge receiving by saying `I see a test message`"
        ),
        "conversation": {
            "id": int(os.getenv("TEST_CONVERSATION_ID", "20")),
            "status": "pending",
            "meta": {"assignee": None},
        },
        "sender": {"id": 123, "type": "user"},
    }

    # Send webhook request
    async with http_client.post(f"{API_BASE_URL}/chatwoot-webhook", json=webhook_payload) as response:
        # We expect 200 OK even if message processing is in background
        assert response.status == 200
        data = await response.json()
        assert "status" in data


async def test_update_labels_endpoint(http_client, test_conversation_id):
    """Test updating labels via API endpoint"""
    test_labels = ["test-label-1", "test-label-2"]

    async with http_client.post(f"{API_BASE_URL}/update-labels/{test_conversation_id}", json=test_labels) as response:
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "success"
        assert "labels" in data


async def test_toggle_priority_endpoint(http_client, test_conversation_id):
    """Test toggling priority via API endpoint"""
    priority_payload = {"priority": "medium"}

    async with http_client.post(
        f"{API_BASE_URL}/toggle-priority/{test_conversation_id}", json=priority_payload
    ) as response:
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "success"
        assert "priority" in data


async def test_custom_attributes_endpoint(http_client, test_conversation_id):
    """Test updating custom attributes via API endpoint"""
    attributes = {"test_key": "test_value", "region": "Test Region"}

    async with http_client.post(
        f"{API_BASE_URL}/update-custom-attributes/{test_conversation_id}", json=attributes
    ) as response:
        assert response.status == 200
        data = await response.json()
        assert data["status"] == "success"
        assert "custom_attributes" in data
