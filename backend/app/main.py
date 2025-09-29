"""
FastAPI application entry point
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import settings
from .middleware import setup_middleware
from ..core.exceptions import (
    TradingAgentsException,
    trading_agents_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from ..core.database import init_db, close_db
from ..api.v1.health import router as health_router
from ..api.v1.auth import router as auth_router
from ..api.v1.analysis import router as analysis_router
from ..api.v1.config import router as config_router
from ..api.v1.websocket import router as websocket_router


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    app.add_exception_handler(TradingAgentsException, trading_agents_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Include routers
    app.include_router(
        health_router,
        prefix=settings.API_V1_STR,
        tags=["health"]
    )
    app.include_router(
        auth_router,
        prefix=f"{settings.API_V1_STR}/auth",
        tags=["authentication"]
    )
    app.include_router(
        analysis_router,
        prefix=f"{settings.API_V1_STR}/analysis",
        tags=["analysis"]
    )
    app.include_router(
        config_router,
        prefix=f"{settings.API_V1_STR}/config",
        tags=["configuration"]
    )
    app.include_router(
        websocket_router,
        prefix=f"{settings.API_V1_STR}",
        tags=["websocket"]
    )
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize database connections and task queue on startup"""
        try:
            await init_db()
            
            # Initialize task queue
            from ..core.task_queue import initialize_task_queue
            await initialize_task_queue()
            
            # Initialize WebSocket manager
            from ..core.websocket_manager import get_websocket_manager
            await get_websocket_manager()
            
            print("Application startup completed")
        except Exception as e:
            print(f"Application startup failed: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Close database connections and shutdown task queue"""
        try:
            # Shutdown task queue
            from ..core.task_queue import shutdown_task_queue
            await shutdown_task_queue()
            
            # Shutdown WebSocket manager
            from ..core.websocket_manager import shutdown_websocket_manager
            await shutdown_websocket_manager()
            
            await close_db()
            print("Application shutdown completed")
        except Exception as e:
            print(f"Application shutdown failed: {e}")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"{settings.PROJECT_NAME} is running",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "docs_url": f"{settings.API_V1_STR}/docs"
        }
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )