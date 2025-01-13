from fastapi import FastAPI

from .api import webhooks
from .database import engine
from .models.database import SQLModel
from .telemetry import setup_telemetry

SQLModel.metadata.create_all(bind=engine)

app = FastAPI(title="Chatwoot AI Handler")
setup_telemetry(app, engine)

app.include_router(webhooks.router,prefix="/api/v1") 