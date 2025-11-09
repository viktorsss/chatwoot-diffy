"""Database and data models package."""

# Database models (SQLAlchemy 2)
from app.db.models import ChatwootMessageBatch, ChatwootUserMessage, Conversation

# DTO schemas (Pydantic v2) - imported from new schemas package
from app.schemas import (
    ChatwootConversation,
    ChatwootMessage,
    ChatwootMeta,
    ChatwootSender,
    ChatwootWebhook,
    ConversationCreate,
    ConversationCreateRequest,
    ConversationPriority,
    ConversationResponse,
    ConversationStatus,
    ConversationUpdateRequest,
    DifyResponse,
)

__all__ = [
    # Database models
    "Conversation",
    "ChatwootMessageBatch",
    "ChatwootUserMessage",
    # DTO schemas
    "ConversationCreate",
    "ConversationCreateRequest",
    "ConversationResponse",
    "ConversationUpdateRequest",
    "ChatwootWebhook",
    "ChatwootSender",
    "ChatwootMeta",
    "ChatwootConversation",
    "ChatwootMessage",
    "DifyResponse",
    "ConversationPriority",
    "ConversationStatus",
]
