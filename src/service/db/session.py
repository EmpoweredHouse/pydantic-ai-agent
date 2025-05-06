"""Database session handling utilities."""

from typing import AsyncGenerator, Callable, AsyncContextManager, TypeAlias
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from src.service.db.base import AsyncSessionLocal

# Type alias for better readability
SessionFactory: TypeAlias = Callable[[], AsyncContextManager[AsyncSession]]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session dependency for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_session_factory() -> AsyncGenerator[SessionFactory, None]:
    """
    Get a factory function that creates database sessions.
    
    Returns a factory function that, when called, returns an async context manager
    that yields a database session. This gives full control over transaction management.
    
    Example usage:
        session_factory = Depends(get_session_factory)
        
        # Use the factory to create a session with an explicit transaction:
        async with session_factory() as session:
            async with session.begin():
                # do database operations
    """
    @asynccontextmanager
    async def create_session() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            yield session
    
    yield create_session