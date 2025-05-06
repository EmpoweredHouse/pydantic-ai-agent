"""Agent-related API models for request/response validation.

This module contains Pydantic models that define the structure and validation
rules for Agent-related API requests and responses.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class AgentRequest(BaseModel):
    """
    Agent request schema for API endpoints.
    
    This model is used to validate client requests to the agent system.
    It contains all necessary information to process a user's query.
    
    Attributes:
        query: The text of the user's query to the agent
        thread_id: ID of the thread to send the query to
    """
    
    query: str
    thread_id: UUID


class AgentResponse(BaseModel):
    """
    Agent response schema for API endpoints.
    
    This model is used to format the agent's response to a query for
    transmission back to API clients. It includes both the response text
    and metadata about where the response is stored.
    
    Attributes:
        thread_id: ID of the thread containing this response
        message_id: ID of the message containing this response
        response: The text content of the agent's response
    """
    
    thread_id: UUID
    message_id: UUID
    response: str
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('thread_id', 'message_id')
    def serialize_uuid(self, uuid_value: UUID) -> str:
        """Serialize UUID fields to strings."""
        return str(uuid_value) 