"""User-related API dependencies."""

from uuid import UUID

from fastapi import Header, HTTPException, status


async def get_user_id(x_user_id: str = Header(..., description="ID of the user making the request")) -> UUID:
    """
    Extract and validate user ID from request headers.
    
    This function extracts the user ID from the X-User-ID header and validates
    that it is a properly formatted UUID.
    
    Args:
        x_user_id: User ID from the X-User-ID header
        
    Returns:
        The validated user ID as a UUID object
        
    Raises:
        HTTPException: If the user ID is missing or invalid
    """
    try:
        return UUID(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid User ID format in X-User-ID header"
        ) 