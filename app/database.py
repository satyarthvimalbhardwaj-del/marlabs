"""
Async database connection and session management.
Implements connection pooling and health checks.
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Global engine instance
engine: AsyncEngine = None


def get_engine() -> AsyncEngine:
    """
    Create and configure async database engine with connection pooling.

    Returns:
        Configured AsyncEngine instance
    """
    global engine

    if engine is None:
        try:
            logger.info(f"Creating database engine for: {settings.DATABASE_URL.split('@')[1]}")

            # Use QueuePool for production, NullPool for testing
            poolclass = NullPool if settings.ENVIRONMENT == "testing" else QueuePool

            engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                future=True,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                poolclass=poolclass,
                connect_args={
                    "server_settings": {"application_name": settings.APP_NAME}
                }
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}", exc_info=True)
            raise

    return engine


# Create async session factory
def get_session_factory() -> async_sessionmaker:
    """
    Create async session factory.

    Returns:
        Configured async_sessionmaker
    """
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )


AsyncSessionLocal = get_session_factory()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with automatic cleanup.

    Yields:
        Database session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created")
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")


async def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in Base metadata.
    """
    try:
        logger.info("Initializing database tables...")
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


async def check_db_connection() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is accessible
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}", exc_info=True)
        return False


async def close_db_connection() -> None:
    """Close database engine and connections."""
    global engine
    if engine:
        try:
            await engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}", exc_info=True)
