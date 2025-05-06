"""Base SQLAlchemy models and engine configuration for SQLite."""

import logging
from uuid import UUID
from typing import Optional, Any, Type, TypeVar, Generic, Union, Dict
from enum import Enum

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import MetaData, TypeDecorator, String

from src.service.core.settings import settings

logger = logging.getLogger(__name__)

# Create a UUID type that stores as string in SQLite
class UUIDType(TypeDecorator[str]):
    """Platform-independent UUID type for SQLite compatibility.
    
    Uses String as storage and converts to/from UUID objects.
    """
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)
    
    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        return value  # Keep as string for SQLite compatibility

# Generic enum type for SQLite compatibility
E = TypeVar('E', bound=Enum)

class EnumType(TypeDecorator[str], Generic[E]):
    """Enum type for SQLite compatibility.
    
    Stores enum values as strings in SQLite.
    """
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class: Type[E], length: int = 50):
        super().__init__(length)
        self.enum_class = enum_class
        
    def process_bind_param(self, value: Optional[Union[E, str, Any]], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)
    
    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        # We need to return str to satisfy the TypeDecorator contract
        # The actual conversion to enum happens at the ORM level
        return value

# Create metadata with naming convention
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

# Create a base class for declarative models
class Base(DeclarativeBase):
    metadata = metadata
    
    # Register basic UUID type handler
    type_annotation_map = {
        UUID: UUIDType(36),
    }

# Function to configure enum types - will be called after Base is defined
def configure_type_mapping() -> None:
    """Configure type mapping for enums.
    
    This is called during initialization to avoid circular imports.
    """
    # Import enums here to avoid circular imports
    from src.service.models.api.message_models import MessageRole
    from src.service.models.api.internal import AgentType
    
    # We need to use dict() with type annotation to avoid mypy errors
    # with mixing different types in the same dictionary
    enum_mappings: Dict[Any, Any] = {
        AgentType: EnumType(AgentType, 50),
        MessageRole: EnumType(MessageRole, 20),
    }
    
    # Update the type_annotation_map with enum mappings
    Base.type_annotation_map.update(enum_mappings)

# Create async engine for SQLite
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.is_dev(),
    connect_args={
        "check_same_thread": False,
        "detect_types": 3  # PARSE_DECLTYPES | PARSE_COLNAMES for better datetime handling
    }
)

# Use AsyncSession for the sessionmaker
AsyncSessionLocal = sessionmaker(  # type: ignore
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create all tables in the database
async def init_db() -> None:
    """Create all tables defined in the models."""
    # Configure type mappings for enums
    configure_type_mapping()
    
    # Import all models to register them with SQLAlchemy
    from src.service.models.database.models import Thread, Message
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or verified")
        
    logger.info("Database initialization complete")
 