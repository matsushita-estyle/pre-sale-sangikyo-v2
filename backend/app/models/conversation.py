"""Conversation models for chat history."""

from pydantic import BaseModel


class Message(BaseModel):
    """Single message in a conversation."""

    message_id: str  # UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: str  # ISO 8601
    search_history: list[dict] | None = None


class Conversation(BaseModel):
    """Conversation session."""

    id: str  # conversation_id (UUID) - partition key
    user_id: str
    title: str  # "KDDI案件について" etc (auto-generated)
    messages: list[Message]
    created_at: str
    updated_at: str
    is_active: bool = True  # For archiving feature
