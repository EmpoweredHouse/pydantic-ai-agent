"""Internal shared models for use within API services.

This module contains internal models that are shared across different domains
but not directly exposed in the API. These models support internal operations
and conversions between layers.
"""

from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel

from src.service.models.api.message_models import MessageRole


class AgentType(str, Enum):
    """
    Available agent types in the system.
    
    Each enum value represents a different specialized agent that can process user queries.
    The agent type determines which agent implementation will handle the user's request.
    """
    BANK_SUPPORT = "bank_support"    # Bank support agent

class ThreadCreate(BaseModel):
    """Thread creation schema for internal use."""
    
    user_id: UUID
    agent_type: AgentType


class MessageCreate(BaseModel):
    """Message creation schema for internal use."""
    
    # Optional ID - allows pre-generating IDs for streaming responses
    # or letting the database generate IDs automatically
    id: Optional[UUID] = None
    
    thread_id: UUID
    role: MessageRole
    
    # Stores the serialized model message for complete context retrieval
    # Must be provided during initialization to ensure all messages have their complete data
    raw_json: bytes


class InternalError(Exception):
    """
    Base class for internal errors in the service.
    
    Provides a common ancestor for all service-specific exceptions.
    """
    
    pass


class ModelConversionError(InternalError):
    """
    Error raised when model conversion fails.
    
    Raised when there is an issue converting between database models
    and API models.
    """
    
    pass
