"""SQLAlchemy 2 database models with dataclass mapping."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Conversation(Base):
    """Conversation table model using SQLAlchemy 2 with dataclass mapping."""

    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(primary_key=True, init=False, autoincrement=True)
    chatwoot_conversation_id: Mapped[str] = mapped_column(index=True)
    dify_conversation_id: Mapped[Optional[str]] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="pending")
    assignee_id: Mapped[Optional[int]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), insert_default=lambda: datetime.now(UTC), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        init=False,
    )


class ChatwootMessageBatch(Base):
    """Persisted groupings of combined Chatwoot user messages."""

    __tablename__ = "chatwoot_message_batch"

    id: Mapped[int] = mapped_column(primary_key=True, init=False, autoincrement=True)
    batch_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), nullable=False)
    dify_conversation_id: Mapped[Optional[str]] = mapped_column(default=None)
    chatwoot_message_ids: Mapped[str] = mapped_column(Text, nullable=False)
    combined_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        nullable=False,
        init=False,
    )
    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        nullable=False,
        init=False,
    )


class ChatwootUserMessage(Base):
    """Individual Chatwoot user messages tracked for debouncing."""

    __tablename__ = "chatwoot_user_message"

    id: Mapped[int] = mapped_column(primary_key=True, init=False, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversation.id"), nullable=False)
    chatwoot_message_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chatwoot_message_batch.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=lambda: datetime.now(UTC),
        nullable=False,
        init=False,
    )
