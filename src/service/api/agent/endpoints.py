"""Agent API endpoints."""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.service.db.session import get_session_factory, SessionFactory
from src.service.models.api import AgentRequest, AgentResponse
from src.service.dependencies.user import get_user_id

from src.service.api.agent.handlers import (
    validate_agent_request,
    run_agent_query,
    stream_agent_query
)

router = APIRouter()

@router.post("/query", response_model=AgentResponse)
async def query_agent(
    agent_request: AgentRequest,
    user_id: UUID = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory)
) -> AgentResponse:
    """
    Send a query to the agent and get a complete response.
    
    The thread_id must be provided to identify which conversation thread to use.
    Threads need to be created separately via the thread endpoints before querying.
    
    Args:
        agent_request: The query request with thread_id and query text
        user_id: ID of the user making the request (from X-User-ID header)
        session_factory: Factory function for database sessions
    """
    # Validate the request and get the thread object
    thread = await validate_agent_request(session_factory, agent_request, user_id)

    # Run agent query with the session factory for explicit transaction control
    return await run_agent_query(
        session_factory=session_factory,
        query=agent_request.query,
        thread=thread
    )


@router.post("/stream")
async def stream_agent(
    agent_request: AgentRequest,
    user_id: UUID = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory)
) -> StreamingResponse:
    """
    Send a query to the agent and stream the response token by token.
    
    The thread_id must be provided to identify which conversation thread to use.
    Threads need to be created separately via the thread endpoints before querying.
    
    Args:
        agent_request: The query request with thread_id and query text
        user_id: ID of the user making the request (from X-User-ID header)
        session_factory: Factory function for database sessions
    """
    # Validate the request and get the thread object
    thread = await validate_agent_request(session_factory, agent_request, user_id)
    
    async def generate_agent_response_stream() -> AsyncGenerator[str, None]:
        """Generate a stream of agent response chunks as JSON lines."""
        # Stream the agent response
        async for chunk in stream_agent_query(
            session_factory=session_factory,
            query=agent_request.query,
            thread=thread
        ):
            # Convert each chunk to JSON
            yield f"{chunk.model_dump_json()}\n"
    
    # Configure stream response with appropriate headers
    return StreamingResponse(
        generate_agent_response_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    ) 
    