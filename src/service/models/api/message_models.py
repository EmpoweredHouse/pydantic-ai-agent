"""Message-related API models for request/response validation.

This module contains Pydantic models that define the structure and validation
rules for Message-related API requests and responses.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

class MessageRole(str, Enum):
    """
    Enumeration of message roles in conversations.
    
    These roles define the sender/creator of each message in a conversation thread
    and determine how messages are displayed and processed.
    
    Attributes:
        USER: Messages created by human users
        ASSISTANT: Messages created by the AI assistant
        SYSTEM: System messages providing context or instructions
        TOOL: Messages from tools or external integrations
    """
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageCreateRequest(BaseModel):
    """
    Message creation request schema for API endpoints.
    
    This model is used to validate client requests to create new messages
    in existing conversation threads.
    
    Attributes:
        content: Text content of the message
        role: Role of the message sender (defaults to user)
    """
    
    content: str
    role: MessageRole = MessageRole.USER


class MessageResponse(BaseModel):
    """
    Message response schema for API endpoints.
    
    This model is used to format and validate message information sent back
    to API clients. It contains both metadata and content from a message.
    
    Attributes:
        id: Unique identifier for the message
        thread_id: ID of the thread this message belongs to
        role: Role of the message sender (user, assistant, etc.)
        content: Human-readable content of the message
        created_at: Timestamp when the message was created
    """
    
    id: UUID
    thread_id: UUID
    role: MessageRole
    content: str

    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('id', 'thread_id')
    def serialize_uuid(self, uuid_value: UUID) -> str:
        """Serialize UUID fields to strings."""
        return str(uuid_value)
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime fields to ISO format strings."""
        return dt.isoformat()
