from fastapi import FastAPI
from .api import webhooks
from .database import engine
from .models.database import Dialogue, SQLModel
from . import config

SQLModel.metadata.create_all(bind=engine)

app = FastAPI(title="Chatwoot AI Handler")

app.include_router(webhooks.router,prefix="/api/v1") 