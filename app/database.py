from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

from . import config

engine = create_engine(
    config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_pre_ping=config.DB_POOL_PRE_PING,
    connect_args={"connect_timeout": 10},  # PostgreSQL specific - connect timeout in seconds
)


def get_session():
    return Session(engine)


SessionLocal = get_session


def get_db():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
