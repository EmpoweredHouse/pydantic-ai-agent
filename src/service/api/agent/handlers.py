"""Agent request handlers for API endpoints."""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status
from src.service.models.database import Thread
from src.service.db.session import SessionFactory
from src.service.models.api import AgentRequest, AgentResponse, AgentResponseChunk
from src.service.models.api.stream_models import ErrorChunk, DoneChunk
from src.service.models.api.errors import ThreadPermissionError, EmptyResponseError, ModelResponseFormatError
from src.service.models.database.errors import ThreadNotFoundError

import logging
logger = logging.getLogger(__name__)

async def validate_agent_request(
    session_factory: SessionFactory,
    agent_request: AgentRequest, 
    user_id: UUID
) -> Thread:
    """
    Validate the agent request and load the thread.
    
    Args:
        session_factory: Factory function that creates database sessions
        agent_request: The request containing query and thread_id
        user_id: The ID of the user making the request
    
    Returns:
        The ThreadResponse API model
        
    Raises:
        HTTPException: For invalid requests or unauthorized access
    """


    try:
        async with session_factory() as db:
            from src.service.core.utils import verify_thread_access
            return await verify_thread_access(db, agent_request.thread_id, user_id)
    except ThreadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ThreadPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )   

async def run_agent_query(
    session_factory: SessionFactory,
    query: str,
    thread: Thread
) -> AgentResponse:
    """
    Run an agent query and get a complete response.
    
    Args:
        session_factory: Factory function that creates database sessions
        query: User query text
        thread: The ThreadResponse API model to query
        
    Returns:
        Agent response with thread_id, response text, and message_id
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    
    try:
        from src.service.api.agent.operations import run_agent_query
        return await run_agent_query(
            session_factory=session_factory, 
            query=query, 
            thread=thread
        )
    except EmptyResponseError as e:
        logger.error(f"Empty response error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ModelResponseFormatError as e:
        logger.error(f"Model response format error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle any unexpected errors with a generic server error
        logger.error(f"Unexpected error running agent query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

async def stream_agent_query(
    session_factory: SessionFactory,
    query: str,
    thread: Thread
) -> AsyncGenerator[AgentResponseChunk, None]:
    """
    Stream an agent query response chunk by chunk.
    
    Args:
        session_factory: Factory function that creates database sessions
        query: User query text
        thread: The Thread model to query
        
    Yields:
        Agent response chunks for streaming
        
    Raises:
        HTTPException: Only raised for request validation errors, not during streaming
    """

    try:
        from src.service.api.agent.operations import stream_agent_query
        async for chunk in stream_agent_query(
            session_factory=session_factory, 
            query=query, 
            thread=thread
        ):
            yield chunk
    except ThreadNotFoundError as e:
        # For streaming, we convert exceptions to error chunks in the stream
        yield ErrorChunk(error="THREAD_NOT_FOUND", error_type=str(e))
    except ThreadPermissionError as e:
        yield ErrorChunk(error="PERMISSION_DENIED", error_type=str(e))
    except EmptyResponseError as e:
        yield ErrorChunk(error="EMPTY_RESPONSE", error_type=str(e))
    except ModelResponseFormatError as e:
        yield ErrorChunk(error="FORMAT_ERROR", error_type=str(e))
    except ValueError as e:
        yield ErrorChunk(error="AGENT_ERROR", error_type=str(e))
    except Exception as e:
        logger.error(f"Unexpected error streaming agent query: {str(e)}", exc_info=True)
        yield ErrorChunk(error="SYSTEM_ERROR", error_type=f"Unexpected error: {str(e)}")
    
    # Send a done event to end the stream properly
    yield DoneChunk() 