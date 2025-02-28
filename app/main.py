import logging
import os

from fastapi import FastAPI

from .api import health, webhooks
from .api.webhooks import lifespan
from .database import async_engine, create_db_tables
from .telemetry import setup_telemetry

# Add before creating FastAPI app
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(title="Chatwoot AI Handler", lifespan=lifespan)
setup_telemetry(app, async_engine)


# Initialize database tables asynchronously
@app.on_event("startup")
async def startup_db_client():
    await create_db_tables()


app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1/health")
