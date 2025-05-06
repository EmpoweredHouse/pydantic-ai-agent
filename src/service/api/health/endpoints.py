"""Health check API endpoints."""

from datetime import datetime, timezone
import socket
from typing import Dict, Any

from fastapi import APIRouter, status

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Check if the service is healthy.
    
    Returns:
        A dictionary with health check information
    """

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "hostname": socket.gethostname(),
        "version": "1.0.0"
    } 