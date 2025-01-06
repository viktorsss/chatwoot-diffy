from sqlmodel import SQLModel, create_engine, Session
from . import config

engine = create_engine(config.DATABASE_URL)

def get_session():
    return Session(engine)

SessionLocal = get_session

def get_db():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine) 