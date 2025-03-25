import logging

import sentry_sdk
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from ..config import (
    DEBUG,
    SENTRY_ATTACH_STACKTRACE,
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    SENTRY_LOG_LEVEL,
    SENTRY_PROFILES_SAMPLE_RATE,
    SENTRY_SEND_DEFAULT_PII,
    SENTRY_TRACES_SAMPLE_RATE,
)


def init_sentry(with_fastapi=True, with_asyncpg=True, with_celery=True, custom_integrations=None):
    """
    Initialize Sentry SDK with appropriate integrations.

    Args:
        with_fastapi (bool): Include FastAPI integration
        with_asyncpg (bool): Include AsyncPG integration
        with_celery (bool): Include Celery integration
        custom_integrations (list): List of custom integration instances to use instead of defaults

    Returns:
        bool: Whether Sentry was initialized
    """
    if not SENTRY_DSN:
        return False

    # Get the log level from config
    log_level = getattr(logging, SENTRY_LOG_LEVEL, logging.WARNING)

    # Setup the logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture INFO and above as breadcrumbs
        event_level=log_level,  # Send specified level and above as events
    )

    # If custom integrations are provided, use those
    if custom_integrations is not None:
        integrations = [sentry_logging] + list(custom_integrations)
    else:
        # Prepare integrations based on parameters
        integrations = [sentry_logging]

        if with_fastapi:
            integrations.append(FastApiIntegration())
            # For FastAPI, also add Starlette integration
            integrations.append(StarletteIntegration())

        if with_asyncpg:
            integrations.append(AsyncPGIntegration())

        if with_celery:
            integrations.append(CeleryIntegration())

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        integrations=integrations,
        enable_tracing=True,
        debug=DEBUG == "True",
        attach_stacktrace=SENTRY_ATTACH_STACKTRACE,
        send_default_pii=SENTRY_SEND_DEFAULT_PII,
        in_app_include=["app"],
    )

    return True
