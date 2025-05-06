"""API router definition combining all endpoints."""

from fastapi import APIRouter, Depends

from src.service.api.agent.endpoints import router as agent_router
from src.service.api.thread.endpoints import router as threads_router
from src.service.api.health.endpoints import router as health_router
from src.service.dependencies.auth import get_api_key
from src.service.dependencies.user import get_user_id

# Create main API router with API key dependency only
api_router = APIRouter(dependencies=[Depends(get_api_key)])

# Include health endpoints - only requires API key
api_router.include_router(health_router, tags=["health"])

# Include endpoints that require both API key and user ID validation
# Add user_id dependency at the router level so all thread endpoints require it
api_router.include_router(
    threads_router, 
    prefix="/threads", 
    tags=["threads"],
    dependencies=[Depends(get_user_id)]
)

# Add user_id dependency at the router level for agent endpoints
api_router.include_router(
    agent_router, 
    prefix="/agent", 
    tags=["agent"],
    dependencies=[Depends(get_user_id)]
) 