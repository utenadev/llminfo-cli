"""Custom error classes for llminfo-cli"""

from typing import Optional


class LLMInfoError(Exception):
    """Base exception for llminfo-cli errors"""

    pass


class APIError(LLMInfoError):
    """Raised when API requests fail"""

    def __init__(
        self, message: str, status_code: Optional[int] = None, provider: Optional[str] = None
    ):
        self.status_code = status_code
        self.provider = provider
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""

    def __init__(
        self, message: str, retry_after: Optional[int] = None, provider: Optional[str] = None
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, provider=provider)


class AuthenticationError(APIError):
    """Raised when API authentication fails"""

    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, status_code=401, provider=provider)


class ConfigurationError(LLMInfoError):
    """Raised when configuration is invalid"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class NetworkError(LLMInfoError):
    """Raised when network operations fail"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(message)
