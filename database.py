"""
Database connection and session management.
Provides both sync and async database sessions.
"""
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Synchronous engine for migrations and sync operations
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,
)

# Asynchronous engine for FastAPI and async operations
async_engine = create_async_engine(
    settings.database_url_async,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,
)

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# SQLite compatibility for development
@event.listens_for(sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite if used."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Synchronous database session context manager.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db() as db:
            jobs = db.query(Job).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous database session context manager.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
        
    Example:
        async with get_async_db() as db:
            result = await db.execute(select(Job))
            jobs = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session.
    
    Yields:
        AsyncSession: Database session for the request
        
    Usage in FastAPI:
        @app.get("/jobs")
        async def get_jobs(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with get_async_db() as session:
        yield session


async def init_db():
    """
    Initialize database - create all tables.
    Should be called on application startup.
    """
    from app.models import Base
    
    try:
        async with async_engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def close_db():
    """
    Close database connections.
    Should be called on application shutdown.
    """
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("Database connections closed")


async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
