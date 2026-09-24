"""
Business exceptions for the application.

These exceptions are raised by the Service Layer and converted
to HTTP responses by the global exception handler.
"""

from typing import Any


class BusinessException(Exception):
    """
    Base class for all business exceptions.

    Attributes:
        message: Human-readable error message.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(BusinessException):
    """
    Raised when a requested resource does not exist.

    Example:
        raise NotFoundError("Service", 999, "Telegram ID")
        # -> "Service with Telegram ID '999' not found"
    """

    def __init__(
        self,
        resource: str,
        identifier: Any,
        identifier_name: str = "id",
    ) -> None:
        super().__init__(
            f"{resource} with {identifier_name} '{identifier}' not found"
        )


class ServiceUnavailableError(BusinessException):
    """
    Raised when a service is inactive or blocked.

    Example:
        raise ServiceUnavailableError("image_processing")
        # -> "Service 'image_processing' is unavailable"
    """

    def __init__(self, service_name: str) -> None:
        super().__init__(
            f"Service '{service_name}' is unavailable"
        )


class AccessDeniedError(BusinessException):
    """
    Raised when a user does not have access to a resource.

    Example:
        raise AccessDeniedError()
        # -> "Access denied"
    """

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message)


class TooManyRequestsError(BusinessException):
    """
    Raised when a rate limit or concurrent task limit is exceeded.

    Example:
        raise TooManyRequestsError(
            "Too many concurrent tasks (limit: 5)"
        )
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class BusinessValidationError(BusinessException):
    """
    Raised when business validation fails.

    Example:
        raise BusinessValidationError(
            "Task name cannot be empty"
        )
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConflictError(BusinessException):
    """
    Raised when an operation conflicts with existing data.

    Example:
        raise ConflictError(
            "Service with name 'api' already exists"
        )
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)