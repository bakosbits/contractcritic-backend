import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    ContractCriticException,
    contractcritic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("app.services.supabase_client").propagate = False
logging.getLogger("app.api.v1.endpoints.contracts").propagate = False
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI backend for ContractCritic - AI-powered contract analysis",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add exception handlers
app.add_exception_handler(ContractCriticException, contractcritic_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
logger.info("Registering API routes...")
app.include_router(api_router, prefix="/api/v1")
logger.info("API routes registered successfully")

# Debug: Print all registered routes
@app.on_event("startup")
async def debug_routes():
    """Debug: Print all registered routes"""
    logger.info("=== Registered Routes ===")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            logger.info(f"{list(route.methods)} {route.path}")
    logger.info("========================")

# Static file serving (for frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend application."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "ContractCritic API is running", "version": settings.app_version}

@app.get("/{path:path}")
async def serve_frontend_routes(path: str):
    """Serve frontend routes (SPA routing)."""
    # Don't intercept API routes
    if path.startswith("api/"):
        return {"error": "API endpoint not found", "path": path}
    
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    file_path = os.path.join(static_dir, path)
    index_path = os.path.join(static_dir, "index.html")
    
    # If the file exists, serve it
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # Otherwise, serve index.html for SPA routing
    elif os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"error": "File not found", "path": path}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production"
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(f"Shutting down {settings.app_name}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
