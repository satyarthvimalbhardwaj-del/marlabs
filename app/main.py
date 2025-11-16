"""
Main FastAPI application entry point.
Configures middleware, routes, and lifecycle events.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import init_db, close_db_connection, check_db_connection
from app.core.logging_config import setup_logging
from app.core.exceptions import BaseAppException
from app.api.v1 import api_router

# Setup logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        # Check database connection
        if await check_db_connection():
            logger.info("Database connection verified")
        else:
            logger.error("Database connection check failed")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")

    try:
        await close_db_connection()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready blog platform API with authentication, approval workflows, and real-time features",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url.path} - Status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}", exc_info=True)
        raise


# Exception handlers
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions."""
    logger.error(f"Application error: {exc.message}", exc_info=True)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns application status and database connectivity.
    """
    logger.debug("Health check requested")

    db_status = "connected" if await check_db_connection() else "disconnected"

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Returns API information and available endpoints.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
