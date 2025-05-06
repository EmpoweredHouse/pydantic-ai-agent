"""API models (Pydantic schemas) for request/response validation.

This module organizes models by domain (threads, messages, agents) for improved
maintainability and separation of concerns.
"""

# Thread domain models
from src.service.models.api.thread_models import (
    ThreadCreateRequest,
    ThreadResponse,
    ThreadDetailResponse
)

# Message domain models
from src.service.models.api.message_models import (
    MessageRole,
    MessageCreateRequest,
    MessageResponse
)

# Agent domain models
from src.service.models.api.agent_models import (
    AgentRequest,
    AgentResponse
)

# Streaming models
from src.service.models.api.stream_models import (
    StreamMessageInfo,
    ThreadCreatedChunk,
    MessageCreatedChunk,
    MessageStartedChunk,
    TextDeltaChunk,
    MessageCompleteChunk,
    ContentChunk,
    ErrorChunk,
    DoneChunk,
    AgentResponseChunk
)

# Internal shared models
from src.service.models.api.internal import (
    InternalError,
    ModelConversionError,
    # Internal model types
    ThreadCreate,
    MessageCreate,
    AgentType
)

# Error exception classes
from src.service.models.api.errors import (
    ThreadPermissionError,
    AgentTypeError,
    EmptyResponseError,
    ModelResponseFormatError
)

__all__ = [
    # Thread domain models
    "ThreadCreateRequest",
    "ThreadResponse",
    "ThreadDetailResponse",
    
    # Message domain models
    "MessageRole",
    "MessageCreateRequest",
    "MessageResponse",
    
    # Agent domain models
    "AgentType",
    "AgentRequest",
    "AgentResponse",
    
    # Streaming models
    "StreamMessageInfo",
    "ThreadCreatedChunk",
    "MessageCreatedChunk",
    "MessageStartedChunk",
    "TextDeltaChunk",
    "MessageCompleteChunk",
    "ContentChunk",
    "ErrorChunk",
    "DoneChunk",
    "AgentResponseChunk",
    
    # Internal shared models
    "InternalError",
    "ModelConversionError",
    "ThreadCreate",
    "MessageCreate",
    
    # Error exception classes
    "ThreadPermissionError",
    "AgentTypeError",
    "EmptyResponseError",
    "ModelResponseFormatError"
] 