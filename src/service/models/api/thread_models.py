"""Thread-related API models for request/response validation.

This module contains Pydantic models that define the structure and validation
rules for Thread-related API requests and responses.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.service.models.api.message_models import MessageResponse
from src.service.models.api.internal import AgentType


class ThreadCreateRequest(BaseModel):
    """
    Model for API request to create a new thread.
    
    Attributes:
        agent_type: Type of agent to associate with this thread
    """
    
    agent_type: AgentType


class ThreadCreate(BaseModel):
    """
    Internal model for thread creation.
    
    Attributes:
        user_id: ID of the user creating the thread
        agent_type: Type of agent to associate with this thread
    """
    
    user_id: UUID
    agent_type: AgentType


class ThreadResponse(BaseModel):
    """
    Model for API response representing a thread.
    
    Attributes:
        id: Unique identifier for the thread
        user_id: ID of the user who owns the thread
        agent_type: Type of agent associated with this thread
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    id: UUID
    user_id: UUID
    agent_type: AgentType
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('id', 'user_id')
    def serialize_uuid(self, uuid_value: UUID) -> str:
        """Serialize UUID fields to strings."""
        return str(uuid_value)
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime fields to ISO format strings."""
        return dt.isoformat()


class ThreadDetailResponse(ThreadResponse):
    """
    Extended thread response model with messages.
    
    Attributes:
        messages: List of messages in the thread
    """
    
    messages: List[MessageResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
