from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

from app import config

# Synchronous engine for Celery tasks and migrations
sync_engine = create_engine(
    config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_pre_ping=config.DB_POOL_PRE_PING,
    connect_args={"connect_timeout": 10},  # PostgreSQL specific - connect timeout in seconds
)

# Async engine for FastAPI endpoints
# Convert the DATABASE_URL to async URL by replacing postgresql:// with postgresql+asyncpg://
async_database_url = config.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_pre_ping=config.DB_POOL_PRE_PING,
    pool_timeout=config.DB_POOL_TIMEOUT,
)


# Sync session for Celery tasks
@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a synchronous session for Celery tasks."""
    with Session(sync_engine) as session:
        yield session


# Keep this for backward compatibility
SessionLocal = get_session


# Async session for FastAPI endpoints
@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for FastAPI endpoints."""
    async with AsyncSession(async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# For FastAPI dependency injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database access."""
    async with AsyncSession(async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_db_tables():
    """Create tables asynchronously at startup."""
    # Use sync_engine for table creation as it's more reliable
    # SQLModel.metadata.create_all() only works with sync engine
    SQLModel.metadata.create_all(sync_engine)
