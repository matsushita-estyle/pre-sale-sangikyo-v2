"""Custom exceptions for the application."""


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        """Initialize NotFoundException.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    """Exception raised when validation fails."""

    def __init__(self, message: str = "Validation error"):
        """Initialize ValidationException.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=400)


class DatabaseException(AppException):
    """Exception raised when database operation fails."""

    def __init__(self, message: str = "Database error"):
        """Initialize DatabaseException.

        Args:
            message: Error message
        """
        super().__init__(message, status_code=500)
