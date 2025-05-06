"""Authentication middleware for API key validation."""

from typing import Optional, Callable, List

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating API key in request headers.
    
    Enforces API key authentication on all configured paths,
    with optional exclusions for specific paths.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        api_key: str,
        api_key_name: str = "X-API-Key",
        exclude_paths: Optional[List[str]] = None,
        is_path_excluded: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        Initialize the API key middleware.
        
        Args:
            app: The ASGI application
            api_key: The valid API key to check against
            api_key_name: The header name for the API key
            exclude_paths: List of paths to exclude from API key validation
            is_path_excluded: Optional function to determine if a path should be excluded
        """
        super().__init__(app)
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.exclude_paths = exclude_paths or []
        self.is_path_excluded = is_path_excluded or self._default_is_path_excluded
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and validate API key if required.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint to call
            
        Returns:
            Either an unauthorized response or the response from the next middleware
        """
        # Skip validation for excluded paths
        if self.is_path_excluded(request.url.path):
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get(self.api_key_name)
        
        # Validate API key
        if not api_key or api_key != self.api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"},
            )
        
        # API key is valid, proceed with request
        return await call_next(request)
    
    def _default_is_path_excluded(self, path: str) -> bool:
        """
        Default implementation to determine if a path is excluded from API key validation.
        
        Args:
            path: The request path
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # Check for exact match
        if path in self.exclude_paths:
            return True
        
        # Check for path prefix matches
        for exclude_path in self.exclude_paths:
            if exclude_path.endswith("*") and path.startswith(exclude_path[:-1]):
                return True
        
        return False 