"""Models for the service API.

This module organizes all models by domain and layer:

1. API Models: Pydantic models for request/response validation
   - Used for validating incoming requests and formatting outgoing responses
   - Defined in the api/ directory with domain-specific files

2. Database Models: SQLAlchemy ORM models for persistence
   - Define database schema and relationships
   - Defined in the database/ directory

Simple Layered Architecture:
- Client <-> API Models <-> Database Models <-> Database

This architecture separates API contracts from database implementation
while keeping the model conversion straightforward.
"""

# API models by domain
from src.service.models.api import (
    # Thread domain
    ThreadCreateRequest, ThreadResponse, ThreadDetailResponse,
    # Message domain
    MessageRole, MessageCreateRequest, MessageResponse,
    # Agent domain
    AgentRequest, AgentResponse,
    # Streaming
    ThreadCreatedChunk, MessageCreatedChunk, MessageStartedChunk,
    TextDeltaChunk, MessageCompleteChunk, AgentResponseChunk,
    # Internal utilities
    InternalError, ModelConversionError, 
    # Internal model types
    ThreadCreate, MessageCreate
)

# Database models by domain
from src.service.models.database import (
    # Thread domain
    Thread,
    # Message domain
    Message
)

__all__ = [
    # API models
    "ThreadCreateRequest", "ThreadResponse", "ThreadDetailResponse",
    "MessageRole", "MessageCreateRequest", "MessageResponse",
    "AgentRequest", "AgentResponse",
    "ThreadCreatedChunk", "MessageCreatedChunk", "MessageStartedChunk",
    "TextDeltaChunk", "MessageCompleteChunk", "AgentResponseChunk",
    "InternalError", "ModelConversionError",
    "ThreadCreate", "MessageCreate",
    
    # Database models
    "Thread", "Message"
] 