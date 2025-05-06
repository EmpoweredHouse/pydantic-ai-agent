"""Database adapters for SQLite operations.

This module provides a clean interface for database operations,
focused solely on SQLite.
"""

from typing import Any, Dict, Optional, List, Type, TypeVar, Generic
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.service.models.database.models import Message, Thread
from src.service.models.api import MessageRole, AgentType

T = TypeVar('T')

class SQLiteAdapter(Generic[T]):
    """Base SQLite adapter for database operations."""
    
    def __init__(self, model_class: Type[Any]):
        """Initialize with a SQLAlchemy model class."""
        self.model_class = model_class
    
    async def save(self, obj: T, session: AsyncSession) -> T:
        """Save an object to the database."""
        session.add(obj)
        await session.flush()
        return obj
    
    async def get_by_id(self, id_value: UUID, session: AsyncSession) -> Optional[T]:
        """Get an object by its ID."""
        stmt = select(self.model_class).where(getattr(self.model_class, 'id') == id_value)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def update(self, obj: T, session: AsyncSession) -> T:
        """Update an object in the database."""
        session.add(obj)
        await session.flush()
        return obj
    
    async def delete(self, obj: T, session: AsyncSession) -> None:
        """Delete an object from the database."""
        await session.delete(obj)
        await session.flush()


class MessageAdapter(SQLiteAdapter[Message]):
    """Adapter for Message model."""
    
    def __init__(self) -> None:
        """Initialize the Message adapter."""
        super().__init__(Message)
    
    async def create_message(
        self, 
        thread_id: UUID, 
        role: MessageRole, 
        content: Dict[str, Any],
        session: AsyncSession
    ) -> Message:
        """Create a new message."""
        message = Message()
        message.thread_id = thread_id
        message.role = role
        message.raw_json_text = json.dumps(content)
            
        session.add(message)
        await session.flush()
        return message
    
    async def get_messages_by_thread_id(
        self, 
        thread_id: UUID, 
        session: AsyncSession
    ) -> List[Message]:
        """Get all messages for a thread."""
        stmt = select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    def get_message_content(self, message: Message) -> Dict[str, Any]:
        """Extract content from a message's JSON text."""
        if message.raw_json_text:
            content = json.loads(message.raw_json_text)
            if isinstance(content, dict):
                return content
        return {}


class ThreadAdapter(SQLiteAdapter[Thread]):
    """Adapter for Thread model."""
    
    def __init__(self) -> None:
        """Initialize the Thread adapter."""
        super().__init__(Thread)
    
    async def create_thread(
        self, 
        user_id: UUID, 
        agent_type: AgentType,
        session: AsyncSession
    ) -> Thread:
        """Create a new thread."""
        thread = Thread()
        thread.user_id = user_id
        thread.agent_type = agent_type

        session.add(thread)
        await session.flush()
        return thread
    
    async def get_threads_by_user_id(
        self, 
        user_id: UUID, 
        session: AsyncSession
    ) -> List[Thread]:
        """Get all threads for a user."""
        stmt = select(Thread).where(Thread.user_id == user_id).order_by(Thread.updated_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


# Create singleton instances of the adapters
message_adapter = MessageAdapter()
thread_adapter = ThreadAdapter() 