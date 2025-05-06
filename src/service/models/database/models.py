"""Database models for SQLite.

This module contains SQLAlchemy ORM models that represent database entities.
All database models are defined in this single file to avoid circular dependencies.

Models:
- Thread: Represents a conversation container between a user and the agent
- Message: Represents individual messages within a thread
"""

from uuid import uuid4, UUID
from typing import List
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.service.db.base import Base
from src.service.models.api.message_models import MessageRole
from src.service.models.api.internal import AgentType


class Thread(Base):
    """
    Thread database model.
    
    Represents a conversation thread between a user and the agent.
    The thread serves as a container for all messages in a conversation.
    
    Attributes:
        id: Unique identifier for the thread
        user_id: ID of the user who owns this thread
        agent_type: Type of agent associated with this thread
        created_at: Timestamp when the thread was created
        updated_at: Timestamp when the thread was last updated
        messages: Relationship to associated Message objects
    """
    
    __tablename__ = "threads"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    agent_type: Mapped[AgentType] = mapped_column(nullable=False)    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Define relationship to messages
    messages: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="thread", 
        cascade="all, delete-orphan"
    )


class Message(Base):
    """
    Message database model.
    
    Represents a single message in a conversation thread.
    Messages can be from either the user or the assistant (or system).
    
    The raw_json_text field contains the serialized message content in a format
    compatible with the underlying AI model. It is stored as text in SQLite.
    
    Attributes:
        id: Unique identifier for the message
        thread_id: ID of the thread this message belongs to
        role: Role of the message sender (user, assistant, system, tool)
        raw_json_text: Serialized message content in AI-compatible format
        created_at: Timestamp when the message was created
        thread: Relationship to the parent Thread object
    """
    
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    thread_id: Mapped[UUID] = mapped_column(ForeignKey("threads.id"), nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(nullable=False)    
    raw_json_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Define relationship to parent thread
    thread: Mapped[Thread] = relationship("Thread", back_populates="messages") 