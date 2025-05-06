"""API authentication dependencies."""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from src.service.core.settings import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from header.
    
    This provides basic API-level authentication without user-specific 
    authentication. It ensures only authorized applications can access the API.
    """
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key 