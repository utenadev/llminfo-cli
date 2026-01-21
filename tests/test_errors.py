"""Tests for error classes"""


from llminfo_cli.errors import (
    LLMInfoError,
    APIError,
    RateLimitError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
)


class TestAPIError:
    """Test APIError class"""

    def test_api_error_basic(self):
        """Test basic APIError creation"""
        error = APIError("API failed")
        assert str(error) == "API failed"
        assert error.status_code is None
        assert error.provider is None

    def test_api_error_with_status_code(self):
        """Test APIError with status code"""
        error = APIError("API failed", status_code=500)
        assert error.status_code == 500
        assert error.provider is None

    def test_api_error_with_provider(self):
        """Test APIError with provider"""
        error = APIError("API failed", provider="openrouter")
        assert error.provider == "openrouter"
        assert error.status_code is None

    def test_api_error_with_all_params(self):
        """Test APIError with all parameters"""
        error = APIError("API failed", status_code=500, provider="openrouter")
        assert error.status_code == 500
        assert error.provider == "openrouter"


class TestRateLimitError:
    """Test RateLimitError class"""

    def test_rate_limit_error_basic(self):
        """Test basic RateLimitError creation"""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.provider is None
        assert error.retry_after is None

    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after"""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_rate_limit_error_with_provider(self):
        """Test RateLimitError with provider"""
        error = RateLimitError("Rate limit exceeded", provider="groq")
        assert error.provider == "groq"
        assert error.status_code == 429

    def test_rate_limit_error_with_all_params(self):
        """Test RateLimitError with all parameters"""
        error = RateLimitError(
            "Rate limit exceeded", retry_after=120, provider="cerebras"
        )
        assert error.retry_after == 120
        assert error.provider == "cerebras"
        assert error.status_code == 429


class TestAuthenticationError:
    """Test AuthenticationError class"""

    def test_auth_error_basic(self):
        """Test basic AuthenticationError creation"""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert error.status_code == 401
        assert error.provider is None

    def test_auth_error_with_provider(self):
        """Test AuthenticationError with provider"""
        error = AuthenticationError("Authentication failed", provider="mistral")
        assert error.provider == "mistral"
        assert error.status_code == 401


class TestConfigurationError:
    """Test ConfigurationError class"""

    def test_config_error_basic(self):
        """Test basic ConfigurationError creation"""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"
        assert error.field is None

    def test_config_error_with_field(self):
        """Test ConfigurationError with field"""
        error = ConfigurationError("Invalid config", field="api_key")
        assert error.field == "api_key"


class TestNetworkError:
    """Test NetworkError class"""

    def test_network_error_basic(self):
        """Test basic NetworkError creation"""
        error = NetworkError("Network failed")
        assert str(error) == "Network failed"
        assert error.original_error is None

    def test_network_error_with_original_error(self):
        """Test NetworkError with original error"""
        original = ValueError("Original error")
        error = NetworkError("Network failed", original_error=original)
        assert error.original_error is original

    def test_network_error_is_llminfo_error(self):
        """Test NetworkError inheritance"""
        error = NetworkError("Network failed")
        assert isinstance(error, LLMInfoError)
