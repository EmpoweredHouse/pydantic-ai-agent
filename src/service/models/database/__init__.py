"""Database models for the service.

This module contains SQLAlchemy ORM models that represent database entities.
Models are organized by domain (threads, messages) and define the database
schema and relationships between entities.

These database models are directly converted to API models when needed
without intermediate layers.
"""

from src.service.models.database.models import Thread, Message
from src.service.models.database.errors import (
    DatabaseError,
    RecordNotFoundError,
    RecordCreationError,
    ThreadNotFoundError
)

__all__ = [
    # Database models
    "Thread", 
    "Message",
    
    # Database errors
    "DatabaseError",
    "RecordNotFoundError",
    "RecordCreationError",
    "ThreadNotFoundError"
] 