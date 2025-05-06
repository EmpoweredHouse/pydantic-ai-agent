"""Database access functions for the API."""

from typing import List, Sequence, cast
from uuid import UUID, uuid4

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from src.service.models.api import MessageCreate, ThreadCreate
from src.service.models.database.errors import RecordCreationError, ThreadNotFoundError
from src.service.models.database.models import Thread, Message
from src.service.models.api.internal import AgentType
import logging

logger = logging.getLogger(__name__)

# Database access functions
async def create_thread(
    db: AsyncSession,
    thread_data: ThreadCreate
) -> Thread:
    """
    Create a new thread.
    
    Args:
        db: Database session
        thread_data: Thread creation data with user_id and agent_type
        
    Returns:
        Created thread as ThreadResponse
        
    Raises:
        RecordCreationError: If thread creation fails
    """
    try:
        # Ensure agent_type is the proper enum object
        agent_type = thread_data.agent_type
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type.lower())
        
        # Get the string value for database storage
        agent_type_value = agent_type.value
        
        # Generate a new UUID for the thread
        thread_id = uuid4()
        
        # Create the thread with explicit ID
        insert_stmt = (
            insert(Thread)
            .values(
                id=thread_id,
                user_id=thread_data.user_id,
                agent_type=agent_type_value
            )
        )
        
        await db.execute(insert_stmt)
        
        # Fetch the newly inserted thread by ID
        query = select(Thread).where(Thread.id == thread_id)
        result = await db.execute(query)
        thread = result.scalars().first()
        
        if not thread:
            raise RecordCreationError("Failed to create thread - no result returned")
        
        return thread
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        raise RecordCreationError(f"Failed to create thread: {str(e)}")

async def get_thread(
    db: AsyncSession,
    thread_id: UUID
) -> Thread:
    """
    Get a thread by ID.
    
    Args:
        db: Database session
        thread_id: ID of the thread to retrieve
        
    Returns:
        Thread if found, None otherwise
    """
    query = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(query)
    
    thread = result.scalars().first()
    
    if not thread:
        raise ThreadNotFoundError(f"Thread with ID {thread_id} not found")
    
    return thread
    

async def get_threads_by_user(
    db: AsyncSession,
    user_id: UUID
) -> Sequence[Thread]:
    """
    Get all threads for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        List of threads belonging to the user, sorted by creation date (newest first)
    """
    query = select(Thread) \
        .where(Thread.user_id == user_id) \
        .order_by(Thread.created_at.desc())
    result = await db.execute(query)
    
    return result.scalars().all()

async def create_message(
    db: AsyncSession, 
    message_data: MessageCreate, 
    model_message: ModelMessage
) -> Message:
    """
    Create a new message.
    
    Args:
        db: Database session
        message_data: The message data to store with serialized raw_json
        model_message: The ModelMessage used for additional processing (if needed)
        
    Returns:
        Created message as a MessageResponse
        
    Raises:
        RecordCreationError: If message creation fails
    """
    try:
        # Prepare values for insert
        values = {
            "thread_id": message_data.thread_id,
            "role": message_data.role,
            "raw_json_text": message_data.raw_json.decode('utf-8')  # Store as text
        }
        
        # Set custom ID if provided
        if message_data.id:
            values["id"] = message_data.id
        else:
            # Generate a UUID if not provided
            values["id"] = uuid4()
        
        # Use proper SQLAlchemy insert statement
        insert_stmt = (
            insert(Message)
            .values(**values)
            .returning(Message)
        )
        
        result = await db.execute(insert_stmt)
        message = result.first()
        
        if not message:
            raise RecordCreationError("Failed to create message")
        
        return cast(Message, message)
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise RecordCreationError(f"Failed to create message: {str(e)}")

async def get_messages_by_thread(
    db: AsyncSession,
    thread_id: UUID
) -> Sequence[Message]:
    """
    Get all messages for a thread.
    
    Args:
        db: Database session
        thread_id: ID of the thread
        
    Returns:
        List of messages in the thread ordered by creation time
    """
    query = select(Message) \
        .where(Message.thread_id == thread_id) \
        .order_by(Message.created_at)
    result = await db.execute(query)
    
    return result.scalars().all()


async def get_model_messages_by_thread(
    db: AsyncSession,
    thread_id: UUID
) -> Sequence[ModelMessage]:
    """
    Get all messages for a thread as Pydantic-AI ModelMessage objects.
    
    This is used to provide message history to the agent for context.
    
    Args:
        db: Database session
        thread_id: ID of the thread
        
    Returns:
        List of ModelMessage objects parsed from raw JSON
    """
    messages: Sequence[Message] = await get_messages_by_thread(db, thread_id)

    model_messages: List[ModelMessage] = []
    for message in messages:
        try:
            model_messages.extend(ModelMessagesTypeAdapter.validate_json(message.raw_json_text))
        except Exception as e:
            # Skip invalid messages but log the error
            logger.warning(f"Failed to parse raw_json for message {message.id}: {str(e)}")
            continue

    return model_messages


async def create_messages_batch(
    db: AsyncSession,
    thread_id: UUID,
    messages_data: List[MessageCreate]
) -> Sequence[Message]:
    """
    Create multiple messages in a single batch operation.
    
    Args:
        db: Database session
        thread_id: UUID of the thread these messages belong to
        messages_data: List of MessageCreate objects with all required data
    
    Returns:
        List of created message responses
        
    Raises:
        RecordCreationError: If message batch creation fails
    """
    if not messages_data:
        return []
    
    try:
        # Prepare all values for bulk insert
        values_list = []
        message_ids = []  # Keep track of all message IDs
        
        for message_data in messages_data:
            # Get or generate the message ID
            message_id = message_data.id if message_data.id else uuid4()
            message_ids.append(message_id)
            
            # Prepare values dict
            values = {
                "id": message_id,
                "thread_id": thread_id,
                "role": message_data.role,
                "raw_json_text": message_data.raw_json.decode('utf-8')  # Store as text
            }
            
            values_list.append(values)
        
        # Execute the insert without RETURNING clause
        insert_stmt = (
            insert(Message)
            .values(values_list)
        )
        
        await db.execute(insert_stmt)
        
        # Now fetch the messages we just inserted using their IDs
        if message_ids:
            query = select(Message).where(Message.id.in_([str(id) for id in message_ids])).order_by(Message.created_at)
            result = await db.execute(query)
            messages = result.scalars().all()
            
            if not messages and messages_data:
                logger.error(f"Failed to retrieve messages after insert. IDs: {message_ids}")
                raise RecordCreationError("Failed to create messages batch")
            
            return messages
        
        return []
    except Exception as e:
        logger.error(f"Error creating messages batch: {str(e)}")
        raise RecordCreationError(f"Failed to create messages batch: {str(e)}")