"""Dify integration-related Pydantic v2 DTO schemas."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DifyResponse(BaseModel):
    """Schema for Dify API response validation and processing."""
    model_config = ConfigDict(from_attributes=True)
    
    event: Optional[str] = Field(default=None, description="Dify event type")
    task_id: Optional[str] = Field(default=None, description="Task identifier")
    id: Optional[str] = Field(default=None, description="Response ID")
    message_id: Optional[str] = Field(default=None, description="Message identifier")
    conversation_id: Optional[str] = Field(default=None, description="Dify conversation ID")
    mode: Optional[str] = Field(default=None, description="Dify mode")
    answer: str = Field(default="", description="AI response content - can be empty")
    response_metadata: Optional[dict] = Field(default=None, description="Additional response metadata")
    created_at: Optional[int] = Field(default=None, description="Creation timestamp")

    @field_validator("answer")
    @classmethod
    def validate_answer_strip_whitespace(cls, v: str) -> str:
        """Strip whitespace from answer but allow empty strings."""
        if v is None:
            return ""
        return v.strip()

    @classmethod
    def error_response(cls) -> "DifyResponse":
        """Create a standardized error response object."""
        return cls(
            answer=(
                "I apologize, but I'm temporarily unavailable. "
                "Please try again later or wait for a human operator to respond."
            )
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump(exclude_none=True)

    def has_valid_answer(self) -> bool:
        """Check if response has a valid, non-empty answer."""
        return bool(self.answer and self.answer.strip())
