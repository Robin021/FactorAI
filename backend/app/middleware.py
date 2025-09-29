"""
Application middleware configuration
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and timing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request completion (in production, use proper logging)
        if settings.DEBUG:
            print(f"Request {request_id}: {request.method} {request.url} - "
                  f"{response.status_code} - {process_time:.3f}s")
        
        return response


def setup_middleware(app):
    """Configure all application middleware"""
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )