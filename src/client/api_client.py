from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator, Dict, List
from uuid import UUID
import httpx

from src.client._env import API_BASE_URL, API_KEY
from src.service.models.api.internal import AgentType
from src.service.models.api.agent_models import AgentResponse
from src.service.models.api.stream_models import AgentResponseChunk, parse_event_chunk
from src.service.models.api.thread_models import ThreadResponse, ThreadDetailResponse


class ApiClient:
    """Client for communicating with the backend API."""
    
    def __init__(self, base_url: str = API_BASE_URL, api_key: str = API_KEY):
        """Initialize the API client with base URL and API key."""
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        }
        
    def _generate_uuid_from_google_id(self, google_user_id: str) -> UUID:
        namespace_uuid = UUID("00000000-0000-0000-0000-000000000000")

        # Generate a UUID based on the namespace and Google user ID
        unique_uuid = uuid.uuid5(namespace_uuid, google_user_id)

        return unique_uuid

    def _get_user_id(self, email: str) -> str:
        """Get the user ID from the email"""
    
        return str(self._generate_uuid_from_google_id(email))
 
    
    def _get_headers(self, email: str | None) -> Dict[str, str]:
        """Get request headers with user ID."""
        headers = self.headers.copy()
        if email is not None:
            headers["X-User-ID"] = self._get_user_id(email)
        return headers
    
    async def create_thread(self, agent_type: str, user_email: str) -> ThreadResponse:
        """
        Create a new conversation thread.
        
        Args:
            agent_type: The type of agent to use (prd, rfp, mission, challenge)
            
        Returns:
            Thread data with id, user_id, agent_type, created_at, and updated_at
        """
        async with httpx.AsyncClient() as client:
            # Ensure agent_type is a valid value
            valid_types = [agent.value for agent in AgentType]
            if agent_type not in valid_types:
                raise ValueError(f"Invalid agent type: {agent_type}. Must be one of: {', '.join(valid_types)}")
                
            # Simple JSON payload with the agent_type string
            payload = {"agent_type": agent_type}
                
            response = await client.post(
                f"{self.base_url}/api/v1/threads",
                headers=self._get_headers(user_email),
                json=payload
            )
                
            response.raise_for_status()
            return ThreadResponse.model_validate(response.json())
    
    async def get_threads(self, user_email: str) -> List[ThreadResponse]:
        """
        Get all threads for the current user.
        
        Returns:
            List of thread data objects
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/threads",
                headers=self._get_headers(user_email)
            )
            response.raise_for_status()
            return [ThreadResponse.model_validate(thread) for thread in response.json()]
    
    async def get_thread(self, thread_id: UUID, user_email: str) -> ThreadDetailResponse:
        """
        Get a specific thread with its messages.
        
        Args:
            thread_id: UUID of the thread to retrieve
            
        Returns:
            Thread data with messages
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/threads/{thread_id}",
                headers=self._get_headers(user_email)
            )
            response.raise_for_status()
            return ThreadDetailResponse.model_validate(response.json())
    
    async def query_agent(self, thread_id: UUID, query: str, user_email: str) -> AgentResponse:
        """
        Send a query to the agent and get a complete response.
        
        Args:
            thread_id: UUID of the thread
            query: Text query to send to the agent
            
        Returns:
            Agent response data
        """
        async with httpx.AsyncClient() as client:
            payload = {"thread_id": str(thread_id), "query": query}
                
            response = await client.post(
                f"{self.base_url}/api/v1/agent/query",
                headers=self._get_headers(user_email),
                json=payload
            )
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())
    
    async def stream_agent_query(self, thread_id: UUID, query: str, user_email: str) -> AsyncGenerator[AgentResponseChunk, None]:
        """
        Send a query to the agent and stream the response.
        
        Args:
            thread_id: UUID of the thread
            query: Text query to send to the agent
            
        Yields:
            AgentResponseChunk models representing the streaming response chunks
            
        Raises:
            ValidationError: If the API returns a response that doesn't match our models
            HTTPStatusError: If the API returns an error status code
        """
        async with httpx.AsyncClient() as client:
            payload = {"thread_id": str(thread_id), "query": query}
                
            async with client.stream(
                "POST",
                f"{self.base_url}/api/v1/agent/stream",
                headers=self._get_headers(user_email),
                json=payload,
                timeout=300.0  # Longer timeout for streaming responses
            ) as response:
                response.raise_for_status()
                # Stream JSON lines (newline-delimited JSON)
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        # Process all complete lines except the last one (which might be incomplete)
                        for line in lines[:-1]:
                            if line.strip():  # Skip empty lines
                                data = json.loads(line)
                                yield parse_event_chunk(data)
                        # Keep the last (potentially incomplete) line in the buffer
                        buffer = lines[-1]
                
                # Process any remaining data in the buffer
                if buffer.strip():
                    data = json.loads(buffer)
                    yield parse_event_chunk(data)

    async def check_health(self, timeout: float = 10.0) -> bool:
        """
        Check if the API server is healthy by querying the health endpoint.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if API is healthy and returning status "ok", False otherwise
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/health",
                    headers=self._get_headers(None),
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return bool(data.get("status") == "ok")
                return False
                
            except Exception:
                # Any exception (connection error, timeout) means API is not healthy
                return False

