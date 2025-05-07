"""Utilities for service operations."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.service.db.database import get_thread
from src.service.models.api.errors import ThreadPermissionError
from src.service.models.api import ThreadResponse, MessageResponse
from src.service.models.database import Thread, Message

from pydantic_ai.messages import ModelMessagesTypeAdapter

# Utility function to handle both coroutines and direct results
async def ensure_awaited(obj: Any) -> Any:
    """
    Ensure that a possibly awaitable object is properly awaited.
    
    This function handles a special case in the pydantic-ai library where
    AgentResult.new_messages() is documented as a synchronous function:
    
    def new_messages(self, *, output_tool_return_content: str | None = None) -> list[ModelMessage]
    
    But in some implementations it may actually return a coroutine that needs to be awaited.
    This utility safely handles both cases to prevent runtime errors.
    
    Args:
        obj: Any object that might be a coroutine
        
    Returns:
        The awaited result if obj was a coroutine, otherwise obj itself
    """
    import inspect

    if inspect.iscoroutine(obj):
        return await obj
    return obj


async def verify_thread_access(
    db: AsyncSession,
    thread_id: UUID,
    user_id: UUID
) -> Thread:
    """
    Verify a user has access to a specified thread.
    
    Args:
        session_factory: Factory function to create database sessions
        thread_id: The ID of the thread to verify
        user_id: The ID of the user requesting access
        
    Returns:
        The thread API model if access is granted
        
    Raises:
        ThreadPermissionError: If the user doesn't have permission
    """
    thread = await get_thread(db, thread_id)

    # Check permission - compare as strings to handle SQLite string storage
    if str(thread.user_id) != str(user_id):
        raise ThreadPermissionError(f"User with ID {user_id} does not have permission to access thread with ID {thread_id}")
        
    return thread


# Direct model conversion functions
def db_to_api_thread(
    thread: Thread
) -> ThreadResponse:
    """
    Convert a database Thread model to a ThreadResponse API model.
    
    Args:
        thread: Database Thread model instance
            
    Returns:
        ThreadResponse API model
    """
    from src.service.models.api.internal import AgentType
    
    # For asyncpg driver, we need to access attributes directly
    # Type casting helps satisfy the linter while preserving runtime behavior
    return ThreadResponse(
        id=thread.id,
        user_id=thread.user_id,
        agent_type=AgentType(thread.agent_type),
        created_at=thread.created_at,
        updated_at=thread.updated_at
    )


def db_to_api_message(
    message: Message
) -> MessageResponse:
    """
    Convert a database Message model to a MessageResponse API model.
    
    Args:
        message: Database Message model instance
            
    Returns:
        MessageResponse API model
    """
    from src.service.models.api.message_models import MessageRole
    
    # Make sure we have valid UUIDs
    try:
        message_id = UUID(str(message.id)) if message.id else None
        thread_id = UUID(str(message.thread_id)) if message.thread_id else None
        
        # Check if we have valid values
        if not message_id or not thread_id:
            raise ValueError("Missing required ID fields")
            
        # Use proper type conversion for enums too
        message_role = MessageRole(message.role) if message.role else MessageRole.ASSISTANT
        
        # Create the response with proper types
        return MessageResponse(
            id=message_id,
            thread_id=thread_id,
            role=message_role,
            content=_raw_json_to_content(message.raw_json_text),
            created_at=message.created_at
        )
    except Exception as e:
        # Include detailed error information
        error_message = f"Error converting message to API model: {str(e)}"
        error_message += f" ID: {message.id}, Thread ID: {message.thread_id}"
        error_message += f" Types: ID: {type(message.id)}, Thread ID: {type(message.thread_id)}"
        import logging
        logging.getLogger(__name__).error(error_message)
        raise ValueError(error_message) from e


def _raw_json_to_content(
    raw_json: str
) -> str:
    """
    Extract human-readable content from the raw message data.
    
    This computed field processes the raw JSON data into a format
    suitable for display to users.
    
    Returns:
        Human-readable message content as a string
    """
    if not raw_json:
        return ""
    
    # Use ModelMessagesTypeAdapter to validate and parse the JSON
    model_messages = ModelMessagesTypeAdapter.validate_json(raw_json)
    if not model_messages:
        return ""

    # Collect content from all messages and their applicable parts
    parts_content = []
    for message in model_messages:
        if not message.parts:
            continue
            
        for part in message.parts:
            if part.part_kind == "user-prompt":
                parts_content.append(str(part.content))
            elif part.part_kind == "tool-call":
                parts_content.append(str(part.args))
            elif part.part_kind == "tool-return":
                parts_content.append(str(part.content))
            elif part.part_kind == "retry-prompt":
                parts_content.append(str(part.content))
            elif part.part_kind == "text":
                parts_content.append(str(part.content))
                
    return "\n\n".join(parts_content)

# Add the ensure_uuid utility function
def ensure_uuid(value: Any) -> UUID:
    """
    Safely converts SQLAlchemy _UUID_RETURN or similar types to standard UUID.
    
    This function helps with mypy type compatibility when working with 
    UUID columns from SQLAlchemy models.
    
    Args:
        value: A value that should be a UUID (SQLAlchemy _UUID_RETURN or UUID)
        
    Returns:
        A standard UUID object
        
    Raises:
        ValueError: If the value cannot be converted to a UUID
    """
    if isinstance(value, UUID):
        return value
    
    # If it's some other type (like _UUID_RETURN), convert via string
    return UUID(str(value))
