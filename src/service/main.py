"""FastAPI application factory."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logfire
from logging import basicConfig

from src.service.core.settings import settings
from src.service.api import api_router
from src.service.middleware.auth import ApiKeyMiddleware

logger = logging.getLogger(__name__)

# Configure Logfire first, before creating the app
def configure_logfire_service() -> None:
    """Configure Logfire for the FastAPI service."""
    # Configure logfire with valid parameters
    logfire.configure(
        service_name=settings.PROJECT_NAME,
        scrubbing=False,
        console=logfire.ConsoleOptions(min_log_level="info", verbose=True),
        code_source=logfire.CodeSource(
            repository="https://github.com/EmpoweredHouse/problem-discovery-agent",
            revision="main",
        ),
    )

    # Setup logfire to send logs to logfire.io
    logfire.instrument()

    # Configure logging to send logs to logfire.io
    basicConfig(handlers=[logfire.LogfireLoggingHandler()])
    
# Initialize logging before app creation
configure_logfire_service()

# Create the FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Instrument FastAPI - must be done after app creation but before it starts
logfire.instrument_fastapi(app)

# API Key authentication middleware
app.add_middleware(
    ApiKeyMiddleware,
    api_key=settings.API_KEY,
    api_key_name=settings.API_KEY_NAME,
    exclude_paths=[
        # OpenAPI documentation
        "/docs",
        "/redoc",
        "/api/v1/openapi.json",
        # Static files
        "/static/*",
    ]
)

# CORS middleware (should be last in middleware chain)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create startup event to initialize database
@app.on_event("startup")
async def startup() -> None:
    """Initialize database on startup."""
    logfire.info("Starting application")
    
    # Initialize database tables
    from src.service.db.base import init_db
    await init_db()

# Create shutdown event
@app.on_event("shutdown")
async def shutdown() -> None:
    """Close connections on shutdown."""
    logfire.info("Shutting down application")