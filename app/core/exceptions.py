from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union
import logging

logger = logging.getLogger(__name__)


class ContractCriticException(Exception):
    """Base exception for ContractCritic application."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(ContractCriticException):
    """Authentication related errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(ContractCriticException):
    """Authorization related errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(ContractCriticException):
    """Resource not found errors."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationError(ContractCriticException):
    """Validation related errors."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class FileUploadError(ContractCriticException):
    """File upload related errors."""
    
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ExternalServiceError(ContractCriticException):
    """External service related errors."""
    
    def __init__(self, message: str = "External service error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


async def contractcritic_exception_handler(
    request: Request, 
    exc: ContractCriticException
) -> JSONResponse:
    """Handle custom ContractCritic exceptions."""
    logger.error(f"ContractCritic exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "status_code": exc.status_code
        }
    )


async def http_exception_handler(
    request: Request, 
    exc: HTTPException
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    
    # Format validation errors for better readability
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "details": errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )
