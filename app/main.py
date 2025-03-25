import logging
import os

# Using explicit integrations for more control
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from .api import health, webhooks
from .api.webhooks import lifespan
from .database import async_engine, create_db_tables
from .telemetry import setup_telemetry
from .utils.sentry import init_sentry

# Add before creating FastAPI app
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Initialize Sentry with FastAPI, AsyncPG, and Celery integrations


# Initialize Sentry with configurable integrations
sentry_initialized = init_sentry(
    with_fastapi=True,
    with_asyncpg=True,
    with_celery=True,
    custom_integrations=[
        StarletteIntegration(
            transaction_style="endpoint",  # Use endpoint names for transactions
            failed_request_status_codes={*range(400, 600)},  # Capture 4xx and 5xx errors
        ),
        FastApiIntegration(
            transaction_style="endpoint",  # Use endpoint names for transactions
            failed_request_status_codes={*range(400, 600)},  # Capture 4xx and 5xx errors
        ),
    ],
)

if sentry_initialized:
    logging.info("Sentry initialized for FastAPI application with custom integration settings")

app = FastAPI(title="Chatwoot AI Handler", lifespan=lifespan, debug=os.getenv("DEBUG", "False") == "True")
setup_telemetry(app, async_engine)


# Initialize database tables asynchronously
@app.on_event("startup")
async def startup_db_client():
    await create_db_tables()


app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1/health")
