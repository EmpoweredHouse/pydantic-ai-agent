"""Core agent operations for Pydantic-AI integration."""

from __future__ import annotations
import json

from typing import Optional, AsyncGenerator, List, Sequence
from uuid import UUID, uuid4

from src.service.core.utils import ensure_awaited, db_to_api_message, ensure_uuid
from src.service.db.session import SessionFactory
from src.service.db.database import (
    create_message, 
    get_model_messages_by_thread, 
    create_messages_batch, 
)

from src.service.models.api.errors import (
    EmptyResponseError,
    AgentTypeError,
)
from src.service.models.api.internal import AgentType
from src.service.models.api.message_models import MessageResponse
from src.service.models.api import (
    MessageRole, MessageCreate, 
    AgentResponseChunk, MessageCreatedChunk, 
    MessageStartedChunk, TextDeltaChunk, MessageCompleteChunk,
    StreamMessageInfo, AgentResponse, 
)
from pydantic_ai.messages import (
    ModelResponse, ModelMessagesTypeAdapter, 
    ModelRequest, UserPromptPart, SystemPromptPart, ModelMessage
)
from src.service.models.database import Message, Thread

# Import all available agents
from src.agents.bank_support import support_agent
# Import dependencies for agents
from src.agents.deps import SupportDependencies, DatabaseConn

async def _prepare_agent_messages(
    thread_id: UUID,
    model_messages: List[ModelMessage],
    assistant_message_id: Optional[UUID] = None
) -> List[MessageCreate]:
    """
    Prepare messages from agent result for storage.
    
    Args:
        thread_id: Thread ID
        model_messages: List of ModelMessage objects from agent.new_messages()
        assistant_message_id: Optional pre-generated UUID for the assistant message
                             (used in streaming to match the ID clients are receiving chunks for)
        
    Returns:
        List of MessageCreate objects ready for database storage
    """
    # Track if we've found the first assistant message (for ID assignment)
    found_first_assistant = False
    result = []
    
    for message in model_messages:
        # Determine message role
        role = _determine_message_role(message)
        if not role:
            continue  # Skip messages with unknown roles
            
        # Assign message ID (use pre-generated ID for first assistant message if provided)
        message_id = uuid4()
        if role == MessageRole.ASSISTANT and assistant_message_id and not found_first_assistant:
            message_id = assistant_message_id
            found_first_assistant = True
            
        # Serialize to raw JSON and create the database object
        raw_json = ModelMessagesTypeAdapter.dump_json([message])
        message_data = MessageCreate(
            id=message_id,
            thread_id=thread_id,
            role=role,
            raw_json=raw_json
        )
        
        result.append(message_data)
    
    return result

def _determine_message_role(
    message: ModelMessage
) -> MessageRole:
    """Determine the role of a message."""
    if isinstance(message, ModelRequest):
        # Check if it's a system prompt
        if message.parts and any(isinstance(part, SystemPromptPart) for part in message.parts):
            return MessageRole.SYSTEM
        return MessageRole.USER
        
    elif isinstance(message, ModelResponse):
        return MessageRole.ASSISTANT


async def save_agent_messages(
    session_factory: SessionFactory,
    thread_id: UUID,
    model_messages: List[ModelMessage],
    assistant_message_id: Optional[UUID] = None
) -> MessageResponse:
    """
    Save messages from agent result to database using batch operations.
    
    Args:
        session_factory: Factory function to create database sessions
        thread_id: Thread ID
        model_messages: List of ModelMessage objects from agent.new_messages()
        assistant_message_id: Optional pre-generated UUID for the assistant message
                             (used in streaming to match the ID clients are receiving chunks for)
        
    Returns:
        MessageResponse containing the last message added to database
        
    Raises:
        EmptyResponseError: If no valid messages could be generated or content is empty
        ModelResponseFormatError: If model response has an incompatible format
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Prepare message batch data
        message_batch_data = await _prepare_agent_messages(
            thread_id=thread_id,
            model_messages=model_messages,
            assistant_message_id=assistant_message_id
        )
        
        logger.info(f"Prepared {len(message_batch_data)} messages for thread {thread_id}")
        
        # Use a dedicated session with explicit transaction
        responses: Sequence[Message] = []
        if message_batch_data:
            async with session_factory() as db:
                async with db.begin():
                    responses = await create_messages_batch(db, thread_id, message_batch_data)
                    logger.info(f"Created {len(responses)} messages in database")

        # Return info about the last message
        last_message = responses[-1] if responses else None
        
        if not last_message:
            logger.error("No messages were created in the database")
            raise EmptyResponseError("Failed to generate agent response")

        # Convert the message to API format
        api_message = db_to_api_message(last_message)
        return api_message
    except Exception as e:
        logger.error(f"Error saving agent messages: {str(e)}", exc_info=True)
        # Re-raise with a clear message
        raise ValueError(f"Error saving agent messages: {str(e)}")



async def store_user_message_on_error(
    session_factory: SessionFactory, 
    thread_id: UUID,
    user_message_id: UUID, 
    query: str
) -> None:
    """
    Store the user's message when an error occurs during streaming.
    This ensures the user's message is preserved even if 
    the AI response generation fails.
    
    Args:
        session_factory: Factory function to create database sessions
        thread_id: The thread ID
        user_message_id: Pre-generated ID for the user message
        query: The user's query text
    """
    try:
        # Create a ModelMessage from the user query
        user_model_message = ModelRequest(parts=[UserPromptPart(content=query)])
        raw_json = ModelMessagesTypeAdapter.dump_json([user_model_message])
        
        # Create a MessageCreate object
        user_message_data = MessageCreate(
            id=user_message_id,
            thread_id=thread_id,
            role=MessageRole.USER,
            raw_json=raw_json
        )
        
        # Use a transaction for the write operation
        async with session_factory() as db:
            async with db.begin():
                await create_message(db, user_message_data, user_model_message)
    except Exception:
        # Just silently continue - we're already handling another exception
        pass


# Agent mapping for easy dispatch based on agent_type, right now only bank support
AGENT_MAP = {
    AgentType.BANK_SUPPORT.value: support_agent
}

# Create agent dependencies for running the agent
def create_agent_dependencies(user_id: UUID, agent_type: AgentType) -> SupportDependencies:
    """
    Create dependencies for the specified agent type.
    
    Args:
        user_id: ID of the user making the request
        agent_type: Type of agent to create dependencies for
        
    Returns:
        Dependencies appropriate for the agent type
    """
    if agent_type == AgentType.BANK_SUPPORT:
        # For bank support agent, create a synthetic customer ID from user_id
        # and a mock database connection
        customer_id = int(str(user_id).replace('-', '')[:8], 16) % 10000  # Convert part of UUID to int
        return SupportDependencies(customer_id=customer_id, db=DatabaseConn())
    
    # Default case shouldn't happen as we check agent type earlier
    raise ValueError(f"Unsupported agent type: {agent_type}")

async def run_agent_query(
    session_factory: SessionFactory,
    query: str,
    thread: Thread
) -> AgentResponse:
    """
    Run a query through the Pydantic-AI agent.
    
    Args:
        session_factory: Factory function to create database sessions
        query: The user's query
        thread: The thread to use for the query
        
    Returns:
        AgentResponse with thread information and agent response
        
    Raises:
        EmptyResponseError: If agent produces empty response
        ModelResponseFormatError: If model response format is incompatible
        AgentTypeError: If thread has no valid agent type or type isn't supported
        ValueError: For other agent-specific errors
    """
    
    # Load message history using a read-only session
    async with session_factory() as db:
        message_history = await get_model_messages_by_thread(db, ensure_uuid(thread.id))

    # Validate that agent_type exists
    if not thread.agent_type:
        raise AgentTypeError("Thread must have a valid agent_type")
        
    # Get agent for the specified type
    agent_type = thread.agent_type
    if isinstance(agent_type, str):
        agent_type = AgentType(agent_type)
        
    agent_type_str = agent_type.value
    selected_agent = AGENT_MAP.get(agent_type_str)
    
    # If agent type isn't supported, raise an error
    if not selected_agent:
        raise AgentTypeError(f"Unsupported agent type: {agent_type_str}")

    # Create agent dependencies
    agent_deps = create_agent_dependencies(thread.user_id, agent_type)

    # Run the agent query with dependencies
    agent_result = await selected_agent.run(
        query, 
        message_history=list(message_history),
        deps=agent_deps
    )

    # Get new messages with simplified coroutine handling
    new_messages = await ensure_awaited(agent_result.new_messages())
    print(f"New messages: {new_messages}")
    print(f"Output: {agent_result.output}")
    
    # Store all new messages from the agent result
    result_message = await save_agent_messages(
        session_factory=session_factory, 
        thread_id=ensure_uuid(thread.id), 
        model_messages=new_messages,
    )

    # Return response with the last message ID
    return AgentResponse(
        thread_id=result_message.thread_id,
        message_id=result_message.id,
        response=json.dumps(agent_result.output)
    )

async def stream_agent_query(
    session_factory: SessionFactory,
    query: str,
    thread: Thread
) -> AsyncGenerator[AgentResponseChunk, None]:
    """
    Stream a query through the Pydantic-AI agent, yielding chunks as they're generated.
    
    Args:
        session_factory: Factory function to create database sessions
        query: The user's query
        thread: The thread model to use for the query
        
    Yields:
        AgentResponseChunk objects with data as they're generated
        
    Raises:
        EmptyResponseError: If agent produces empty response
        ModelResponseFormatError: If model response format is incompatible
        AgentTypeError: If thread has no valid agent type or type isn't supported
        ValueError: For other agent-specific errors
    """
    
    # Validate that agent_type exists
    if not thread.agent_type:
        raise AgentTypeError("Thread must have a valid agent_type")
        
    # Get agent for the specified type
    agent_type = thread.agent_type
    if isinstance(agent_type, str):
        agent_type = AgentType(agent_type)
        
    agent_type_str = agent_type.value
    selected_agent = AGENT_MAP.get(agent_type_str)
    
    # If agent type isn't supported, raise an error
    if not selected_agent:
        raise AgentTypeError(f"Unsupported agent type: {agent_type_str}")
    
    # Pre-generate UUIDs that will be used for messages
    user_message_id = uuid4()
    assistant_message_id = uuid4()
    
    # Send user message creation event to the client (UI only, not stored yet)
    yield MessageCreatedChunk(message=StreamMessageInfo(id=user_message_id, role=MessageRole.USER))
    
    # Load message history using a read-only session
    async with session_factory() as db:
        message_history = await get_model_messages_by_thread(db, ensure_uuid(thread.id))

    # Tell the client we're starting to generate the assistant's message
    yield MessageStartedChunk(message_id=assistant_message_id)

    # Create agent dependencies
    agent_deps = create_agent_dependencies(thread.user_id, agent_type)

    try:
        # Use run_stream method instead of stream
        async with selected_agent.run_stream(
            query, 
            message_history=list(message_history),
            deps=agent_deps
        ) as result:
            # Stream tokens as they come with debounce
            async for chunk in result.stream_structured(debounce_by=0.03):
                yield TextDeltaChunk(message_id=assistant_message_id, token=chunk)

            # Store all messages at once with explicit transaction
            # Use our utility function to handle possible coroutines
            messages = await ensure_awaited(result.new_messages())
            await save_agent_messages(
                session_factory=session_factory,
                thread_id=ensure_uuid(thread.id),
                model_messages=messages,
                assistant_message_id=assistant_message_id
            )

            # Signal completion to the client
            yield MessageCompleteChunk(message_id=assistant_message_id)
    except Exception:
        # Store the user message regardless of the exception type
        await store_user_message_on_error(
            session_factory=session_factory,
            thread_id=ensure_uuid(thread.id),
            user_message_id=user_message_id,
            query=query
        )
        
        # Re-raise the exception for handling at the API level
        raise
