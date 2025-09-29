"""
Custom exception classes and handlers
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR


class TradingAgentsException(Exception):
    """Base exception for TradingAgents application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(TradingAgentsException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(TradingAgentsException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationException(TradingAgentsException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class NotFoundException(TradingAgentsException):
    """Exception for resource not found errors"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class AnalysisException(TradingAgentsException):
    """Exception for analysis execution errors"""
    
    def __init__(self, message: str = "Analysis execution failed"):
        super().__init__(message=message, status_code=500)


async def trading_agents_exception_handler(
    request: Request, exc: TradingAgentsException
) -> JSONResponse:
    """Global exception handler for TradingAgents exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Global exception handler for HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions"""
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )