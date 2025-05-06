"""Thread API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.service.dependencies.user import get_user_id
from src.service.api.thread.handlers import create_thread, get_threads_by_user, get_thread_by_id
from src.service.db.session import get_session_factory, SessionFactory
from src.service.models.api import (
    ThreadCreateRequest,
    ThreadResponse,
    ThreadDetailResponse
)

router = APIRouter()

@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_new_thread(
    thread_request: ThreadCreateRequest,
    user_id: UUID = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory)
) -> ThreadResponse:
    """
    Create a new conversation thread.
    
    Args:
        thread_request: Thread creation request with agent type
        user_id: ID of the user creating the thread (from X-User-ID header)
        session_factory: Factory function that creates database sessions
    """

    return await create_thread(session_factory, thread_request, user_id)


@router.get("", response_model=List[ThreadResponse], status_code=status.HTTP_200_OK)
async def get_threads(
    user_id: UUID = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory)
) -> List[ThreadResponse]:
    """
    Get all threads for the specified user.
    
    Args:
        user_id: ID of the user to get threads for (from X-User-ID header)
        session_factory: Factory function that creates database sessions
    """

    return await get_threads_by_user(session_factory, user_id)


@router.get("/{thread_id}", response_model=ThreadDetailResponse, status_code=status.HTTP_200_OK)
async def get_thread(
    thread_id: UUID,
    user_id: UUID = Depends(get_user_id),
    session_factory: SessionFactory = Depends(get_session_factory)
) -> ThreadDetailResponse:
    """
    Get a specific thread by ID with its messages.
    
    Args:
        thread_id: ID of the thread to retrieve
        user_id: ID of the user requesting the thread (from X-User-ID header)
        session_factory: Factory function that creates database sessions
    """
    return await get_thread_by_id(session_factory, thread_id, user_id)
