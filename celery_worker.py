import logging

from app.tasks import celery_app
from app.utils.sentry import init_sentry

# Initialize Sentry for Celery workers with only Celery integration
if init_sentry(with_fastapi=False, with_asyncpg=False, with_celery=True):
    logging.info("Celery worker: Sentry initialized")

if __name__ == "__main__":
    celery_app.start()
