"""Thread request handlers for API endpoints."""

from typing import List, Sequence
from uuid import UUID
from fastapi import HTTPException, status

from src.service.core.utils import verify_thread_access, db_to_api_message, db_to_api_thread
from src.service.db.database import get_messages_by_thread

from src.service.db.session import SessionFactory
from src.service.models.api import (
    ThreadCreate,
    ThreadCreateRequest,
    ThreadResponse,
    ThreadDetailResponse
)
from src.service.models.database.errors import ThreadNotFoundError, RecordCreationError
from src.service.models.api.errors import ThreadPermissionError
from src.service.models.database.models import Thread, Message

async def create_thread(
    session_factory: SessionFactory,
    thread_request: ThreadCreateRequest,
    user_id: UUID
) -> ThreadResponse:
    """
    Create a new conversation thread.
    
    Args:
        session_factory: Factory function that creates database sessions
        thread_request: Thread creation request with agent type
        user_id: ID of the user creating the thread
        
    Returns:
        Created thread
    """

    try:
        # Create internal model with user_id
        thread_create = ThreadCreate(
            user_id=user_id,
            agent_type=thread_request.agent_type
        )
        
        from src.service.db.database import create_thread
        async with session_factory() as db:
            async with db.begin():
                thread = await create_thread(db, thread_create)
        
        return db_to_api_thread(thread)
    except RecordCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create thread: {str(e)}"
        )

async def get_threads_by_user(
    session_factory: SessionFactory,
    user_id: UUID
) -> List[ThreadResponse]:
    """
    Get all threads for the specified user.
    
    Args:
        session_factory: Factory function that creates database sessions
        user_id: ID of the user to get threads for
        
    Returns:
        List of threads belonging to the user
    """
    from src.service.db.database import get_threads_by_user

    try:
        async with session_factory() as db:
            # Read-only operation, no transaction needed
            return [db_to_api_thread(thread) for thread in await get_threads_by_user(db, user_id)]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def get_thread_by_id(
    session_factory: SessionFactory,
    thread_id: UUID,
    user_id: UUID
) -> ThreadDetailResponse:
    """
    Get a thread by ID with its messages.
    
    Args:
        session_factory: Factory function that creates database sessions
        thread_id: ID of the thread to get
        user_id: ID of the user to get threads for
        
    Returns:
        Thread detail
    """
    try: 
        async with session_factory() as db:
            # Verify access and get thread
            thread: Thread = await verify_thread_access(db, thread_id, user_id)
            # Get messages for thread
            messages: Sequence[Message] = await get_messages_by_thread(db, thread_id)
            
            # Create a ThreadDetailResponse with messages
            thread_detail = ThreadDetailResponse(
                id=thread.id,
                user_id=thread.user_id,
                agent_type=thread.agent_type,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                messages=[db_to_api_message(message) for message in messages]
            )
            
            return thread_detail 
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
    