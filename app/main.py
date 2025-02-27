import logging
import os

from fastapi import FastAPI

from .api import health, webhooks
from .api.webhooks import lifespan
from .database import engine
from .models.database import SQLModel
from .telemetry import setup_telemetry

SQLModel.metadata.create_all(bind=engine)

# Add before creating FastAPI app
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(title="Chatwoot AI Handler", lifespan=lifespan)
setup_telemetry(app, engine)

app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1/health")
