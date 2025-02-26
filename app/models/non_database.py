from enum import Enum


class ConversationPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = None


class ConversationStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    PENDING = "pending"
