import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()

# API base URL - get from environment or use default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        yield client


async def test_health_endpoint(http_client):
    """Test the health check endpoint"""
    response = await http_client.get("/health")
    assert response.status_code == 200
    data = response.json()
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
    response = await http_client.post("/chatwoot-webhook", json=webhook_payload)
    # We expect 200 OK even if message processing is in background
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


async def test_update_labels_endpoint(http_client, test_conversation_id):
    """Test updating labels via API endpoint"""
    test_labels = ["test-label-1", "test-label-2"]

    response = await http_client.post(f"/update-labels/{test_conversation_id}", json=test_labels)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "labels" in data


async def test_toggle_priority_endpoint(http_client, test_conversation_id):
    """Test toggling priority via API endpoint"""
    priority_payload = {"priority": "medium"}

    response = await http_client.post(
        f"/toggle-priority/{test_conversation_id}", json=priority_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "priority" in data


async def test_custom_attributes_endpoint(http_client, test_conversation_id):
    """Test updating custom attributes via API endpoint"""
    attributes = {"test_key": "test_value", "region": "Test Region"}

    response = await http_client.post(
        f"/update-custom-attributes/{test_conversation_id}", json=attributes
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "custom_attributes" in data
