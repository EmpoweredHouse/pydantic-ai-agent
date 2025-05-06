"""Streaming-related API models for request/response validation.

This module contains Pydantic models that define the structure and validation
rules for streaming API responses, particularly for real-time agent interactions.
"""

from enum import Enum
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel
from src.service.models.api.message_models import MessageRole


class EventType(Enum):
    """
    Enum defining all possible event types for streaming responses.
    
    These values represent the different kinds of events that can occur
    during an agent streaming session.
    """
    THREAD_CREATED = "thread_created"
    MESSAGE_CREATED = "message_created"
    MESSAGE_STARTED = "message_started"
    MESSAGE_CHUNK = "message_chunk"
    TOKEN = "token"
    MESSAGE_COMPLETE = "message_complete"
    CONTENT = "content"
    ERROR = "error"
    DONE = "done"


class StreamMessageInfo(BaseModel):
    """
    Basic message information for streaming events.
    
    Contains minimal information about a message in a streaming context.
    
    Attributes:
        id: Unique identifier for the message
        role: Role of the message sender (user, assistant, etc.)
    """
    
    id: UUID
    role: MessageRole


class ThreadCreatedChunk(BaseModel):
    """
    Stream chunk for thread creation events.
    
    Sent when a new conversation thread is created during streaming.
    
    Attributes:
        event: Event type identifier, always "thread_created"
        thread_id: ID of the newly created thread
    """
    
    event: EventType = EventType.THREAD_CREATED
    thread_id: UUID


class MessageCreatedChunk(BaseModel):
    """
    Stream chunk for message creation events.
    
    Sent when a new message is created during streaming.
    
    Attributes:
        event: Event type identifier, always "message_created"
        message: Information about the created message
    """
    
    event: EventType = EventType.MESSAGE_CREATED
    message: StreamMessageInfo


class MessageStartedChunk(BaseModel):
    """
    Stream chunk for message generation start events.
    
    Sent when the agent begins generating a response message.
    
    Attributes:
        event: Event type identifier, always "message_started"
        message_id: ID of the message being generated
    """
    
    event: EventType = EventType.MESSAGE_STARTED
    message_id: UUID


class MessageChunk(BaseModel):
    """
    Stream chunk for message content.
    
    Contains a piece of content to add to the message being generated.
    
    Attributes:
        event: Event type identifier, always "message_chunk"
        message_id: ID of the message being generated
        content: Text content to add to the message
    """
    
    event: EventType = EventType.MESSAGE_CHUNK
    message_id: UUID
    content: str


class TextDeltaChunk(BaseModel):
    """
    Stream chunk for incremental text updates.
    
    Contains only the new incremental text since the last chunk,
    not the accumulated message content.
    
    Attributes:
        event: Event type identifier, always "token"
        message_id: ID of the message being generated
        token: New text fragment to append to the message
    """
    
    event: EventType = EventType.TOKEN
    message_id: UUID
    token: str


class MessageCompleteChunk(BaseModel):
    """
    Stream chunk for message completion events.
    
    Sent when a message generation is complete.
    
    Attributes:
        event: Event type identifier, always "message_complete"
        message_id: ID of the completed message
    """
    
    event: EventType = EventType.MESSAGE_COMPLETE
    message_id: UUID


class ContentChunk(BaseModel):
    """
    Generic content chunk for streaming responses.
    
    Contains delta text content for incremental updates.
    
    Attributes:
        event: Event type identifier, always "content"
        delta: Text content to add to the message
    """
    
    event: EventType = EventType.CONTENT
    delta: str


class ErrorChunk(BaseModel):
    """
    Error response for streaming endpoints.
    
    Sent when an error occurs during streaming.
    
    Attributes:
        event: Event type identifier, always "error"
        error: Human-readable error message
        error_type: Machine-readable error type identifier
    """
    
    event: EventType = EventType.ERROR
    error: str
    error_type: str


class DoneChunk(BaseModel):
    """
    Signal for stream completion.
    
    Sent as the final chunk in a stream to indicate completion.
    
    Attributes:
        event: Event type identifier, always "done"
    """
    
    event: EventType = EventType.DONE


# Type union of all streaming chunk types
AgentResponseChunk = ThreadCreatedChunk | MessageCreatedChunk | MessageStartedChunk | TextDeltaChunk | MessageChunk | MessageCompleteChunk | ContentChunk | ErrorChunk | DoneChunk 


def parse_event_chunk(data: Dict[str, Any]) -> AgentResponseChunk:
    """
    Parse a JSON event chunk into the appropriate AgentResponseChunk model.
    
    This utility function centralizes the logic for converting raw event data
    into typed Pydantic models based on the event type.
    
    Args:
        data: JSON data dictionary from the API response
            
    Returns:
        An instance of the appropriate AgentResponseChunk subclass
            
    Raises:
        ValueError: If the event type is unknown
    """
    event_type = data.get("event", "")
    
    if event_type == EventType.THREAD_CREATED.value:
        return ThreadCreatedChunk.model_validate(data)
    elif event_type == EventType.MESSAGE_CREATED.value:
        return MessageCreatedChunk.model_validate(data)
    elif event_type == EventType.MESSAGE_STARTED.value:
        return MessageStartedChunk.model_validate(data)
    elif event_type == EventType.MESSAGE_CHUNK.value:
        return MessageChunk.model_validate(data)
    elif event_type == EventType.TOKEN.value:
        return TextDeltaChunk.model_validate(data)
    elif event_type == EventType.MESSAGE_COMPLETE.value:
        return MessageCompleteChunk.model_validate(data)
    elif event_type == EventType.CONTENT.value:
        return ContentChunk.model_validate(data)
    elif event_type == EventType.ERROR.value:
        return ErrorChunk.model_validate(data)
    elif event_type == EventType.DONE.value:
        return DoneChunk.model_validate(data)
    else:
        raise ValueError(f"Unknown event type: {event_type}") 