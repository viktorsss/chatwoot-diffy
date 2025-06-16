"""
Error handling utilities for consistent API error responses.
"""

import functools
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error: str
    message: str
    operation: Optional[str] = None
    conversation_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class DatabaseError(Exception):
    """Custom exception for database-related errors."""

    def __init__(self, message: str, operation: str, conversation_id: Optional[int] = None):
        self.message = message
        self.operation = operation
        self.conversation_id = conversation_id
        super().__init__(message)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def handle_api_errors(operation_name: str):
    """
    Decorator for consistent error handling across API endpoints.

    Args:
        operation_name: Description of the operation for logging/error messages
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except HTTPException:
                # Re-raise HTTPExceptions as-is (they're already properly formatted)
                raise

            except ValueError as e:
                # Validation errors
                logger.error(f"Validation error in {operation_name}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=422,
                    detail={"error": "Validation error", "operation": operation_name, "message": str(e)},
                ) from e

            except Exception as e:
                # Database transaction errors and other unexpected errors
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)

                # The six-line pattern handles database rollbacks automatically
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Internal server error",
                        "operation": operation_name,
                        "message": f"Failed to {operation_name.lower()}",
                    },
                ) from e

        return wrapper

    return decorator


def handle_database_transaction_error(
    error: Exception, operation: str, conversation_id: Optional[int] = None
) -> HTTPException:
    """
    Handle database transaction errors specifically for six-line pattern.

    Args:
        error: The original exception
        operation: Description of the operation that failed
        conversation_id: Optional conversation ID for context

    Returns:
        HTTPException with structured error response
    """
    error_msg = str(error)

    # Log the full error with context
    logger.error(
        f"Database transaction error in {operation}: {error_msg}",
        extra={"operation": operation, "conversation_id": conversation_id, "error_type": type(error).__name__},
        exc_info=True,
    )

    # Check for specific SQLAlchemy transaction errors
    if "closed transaction" in error_msg.lower():
        detail = ErrorResponse(
            error="Database transaction error",
            message="Transaction was closed unexpectedly. The operation has been rolled back automatically.",
            operation=operation,
            conversation_id=conversation_id,
            details={"error_type": "closed_transaction"},
        )
    elif "rollback" in error_msg.lower():
        detail = ErrorResponse(
            error="Database rollback",
            message="Database operation was rolled back due to an error.",
            operation=operation,
            conversation_id=conversation_id,
            details={"error_type": "rollback"},
        )
    else:
        detail = ErrorResponse(
            error="Database error",
            message="A database operation failed unexpectedly.",
            operation=operation,
            conversation_id=conversation_id,
            details={"error_type": "general_db_error"},
        )

    return HTTPException(status_code=500, detail=detail.model_dump())


def handle_validation_error(error: Exception, operation: str, field: Optional[str] = None) -> HTTPException:
    """
    Handle validation errors with structured response.

    Args:
        error: The original validation exception
        operation: Description of the operation that failed
        field: Optional field name that caused the validation error

    Returns:
        HTTPException with structured error response
    """
    error_msg = str(error)

    logger.error(
        f"Validation error in {operation}: {error_msg}",
        extra={"operation": operation, "field": field, "error_type": type(error).__name__},
    )

    detail = ErrorResponse(
        error="Validation error", message=error_msg, operation=operation, details={"field": field} if field else None
    )

    return HTTPException(status_code=422, detail=detail.model_dump())


def log_operation_start(operation: str, **context) -> None:
    """Log the start of an operation with context."""
    logger.info(f"Starting {operation}", extra=context)


def log_operation_success(operation: str, **context) -> None:
    """Log successful completion of an operation."""
    logger.info(f"Successfully completed {operation}", extra=context)


def log_operation_error(operation: str, error: Exception, **context) -> None:
    """Log an error during an operation with full context."""
    logger.error(
        f"Error in {operation}: {str(error)}", extra={**context, "error_type": type(error).__name__}, exc_info=True
    )
