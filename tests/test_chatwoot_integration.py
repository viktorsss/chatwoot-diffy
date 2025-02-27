import random
import string
from datetime import datetime, timezone

import pytest

# Mark all tests in this file as requiring the event loop
pytestmark = pytest.mark.asyncio


# Helper function to generate random strings for testing
def random_string(length=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


async def test_chatwoot_connection(chatwoot_handler, wait_for_service):
    """Test that we can connect to Chatwoot"""

    async def check_chatwoot():
        teams = await chatwoot_handler.get_teams()
        return len(teams) > 0

    # Wait for Chatwoot to be available
    is_available = await wait_for_service(check_chatwoot)
    assert is_available, "Chatwoot service is not available"

    # Get teams to verify connection
    teams = await chatwoot_handler.get_teams()
    assert len(teams) > 0, "Expected at least one team in Chatwoot"


async def test_send_message(chatwoot_handler, test_conversation_id):
    """Test sending a message to a conversation"""
    message = (
        f"Test message {random_string()} at {datetime.now(timezone.utc).isoformat()}"
        "Acknowledge receiving by saying `I see a test message`"
    )
    # Send a message (as a private note to avoid disturbing real conversations)
    result = await chatwoot_handler.send_message(conversation_id=test_conversation_id, message=message, private=True)

    assert result is not None
    assert "id" in result, "Expected response to contain message ID"


async def test_update_conversation_status(chatwoot_handler, test_conversation_id):
    """Test updating conversation status"""
    # First get current status
    conversation_data = await chatwoot_handler.get_conversation_data(test_conversation_id)
    original_status = conversation_data.get("status")

    # Choose a different status than the current one
    statuses = ["open", "pending"]
    new_status = statuses[0] if original_status != statuses[0] else statuses[1]

    # Update status
    result = await chatwoot_handler.toggle_status(conversation_id=test_conversation_id, status=new_status)

    assert result is not None

    # Verify status was changed
    updated_conversation = await chatwoot_handler.get_conversation_data(test_conversation_id)
    assert updated_conversation.get("status") == new_status

    # Reset to original status
    await chatwoot_handler.toggle_status(conversation_id=test_conversation_id, status=original_status)


async def test_add_labels(chatwoot_handler, test_conversation_id):
    """Test adding labels to a conversation"""
    test_label = f"test-label-{random_string(5)}"

    # Add a label
    result = await chatwoot_handler.add_labels(conversation_id=test_conversation_id, labels=[test_label])

    assert result is not None

    # Verify label was added
    conversation_data = await chatwoot_handler.get_conversation_data(test_conversation_id)
    labels = conversation_data.get("labels", [])
    assert test_label in labels, f"Expected label {test_label} to be added"


async def test_update_custom_attributes(chatwoot_handler, test_conversation_id):
    """Test updating custom attributes"""
    test_attribute_key = f"test_attr_{random_string(5)}"
    test_attribute_value = f"value_{random_string(5)}"

    # Update custom attributes
    result = await chatwoot_handler.update_custom_attributes(
        conversation_id=test_conversation_id, custom_attributes={test_attribute_key: test_attribute_value}
    )

    assert result is not None

    # Verify attribute was added
    conversation_data = await chatwoot_handler.get_conversation_data(test_conversation_id)
    custom_attributes = conversation_data.get("custom_attributes", {})
    assert test_attribute_key in custom_attributes, f"Expected attribute {test_attribute_key} to be added"
    assert custom_attributes[test_attribute_key] == test_attribute_value


async def test_toggle_priority(chatwoot_handler, test_conversation_id):
    """Test toggling priority of a conversation"""
    priorities = ["high", "medium", "low"]

    # Get current priority
    conversation_data = await chatwoot_handler.get_conversation_data(test_conversation_id)
    original_priority = conversation_data.get("priority")

    # Choose a different priority
    new_priority = next((p for p in priorities if p != original_priority), priorities[0])

    # Set new priority
    result = await chatwoot_handler.toggle_priority(conversation_id=test_conversation_id, priority=new_priority)

    assert result is not None

    # Verify priority was changed
    updated_conversation = await chatwoot_handler.get_conversation_data(test_conversation_id)
    assert updated_conversation.get("priority") == new_priority

    # Reset to original priority
    await chatwoot_handler.toggle_priority(
        conversation_id=test_conversation_id,
        priority=original_priority or "medium",  # Default to medium if original was None
    )


async def test_error_handling(chatwoot_handler):
    """Test error handling when using invalid conversation ID"""
    invalid_id = 99999999  # Assuming this ID doesn't exist

    # Attempt to get conversation data
    with pytest.raises(Exception):  # noqa: B017
        await chatwoot_handler.get_conversation_data(invalid_id)
