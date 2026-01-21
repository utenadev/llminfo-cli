"""Tests for provider implementations"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from llminfo_cli.providers import get_provider, get_providers
from llminfo_cli.providers.openrouter import OpenRouterProvider
from llminfo_cli.providers.generic import GenericProvider, ProviderFactory
from llminfo_cli.providers.parsers import OpenAICompatibleParser
from llminfo_cli.errors import AuthenticationError, RateLimitError, APIError, NetworkError


@pytest.mark.asyncio
async def test_openrouter_get_models():
    """Test fetching models from OpenRouter"""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response_data = {
        "data": [
            {
                "id": "openai/gpt-4o-mini:free",
                "name": "GPT-4o Mini (Free)",
                "context_length": 128000,
                "pricing": {"prompt": "0.0", "completion": "0.0"},
            },
            {
                "id": "google/gemini-1.5-flash:free",
                "name": "Gemini 1.5 Flash (Free)",
                "context_length": 1000000,
                "pricing": {"prompt": "0.0", "completion": "0.0"},
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        models = await provider.get_models()

        assert len(models) == 2
        assert models[0].id == "openai/gpt-4o-mini:free"
        assert models[1].context_length == 1000000


@pytest.mark.asyncio
async def test_openrouter_get_models_no_api_key():
    """Test error when API key is not set"""
    import os

    original_key = os.environ.get("OPENROUTER_API_KEY")

    try:
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]

        provider = OpenRouterProvider(api_key=None)

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable not set"):
            await provider.get_models()
    finally:
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_openrouter_get_credits():
    """Test fetching credits from OpenRouter"""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response_data = {
        "data": {
            "total_credits": 100.0,
            "total_usage": 25.5,
        }
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        credits = await provider.get_credits()

        assert credits is not None
        assert credits.total_credits == 100.0
        assert credits.usage == 25.5
        assert credits.remaining == 74.5


def test_provider_name():
    """Test provider name property"""
    provider = OpenRouterProvider(api_key="test_key")
    assert provider.provider_name == "openrouter"


@pytest.mark.asyncio
async def test_generic_provider_get_models():
    """Test fetching models from a generic provider (Groq)"""
    provider = get_provider("groq", api_key="test_key")

    mock_response_data = {
        "data": [
            {
                "id": "llama3-70b-8192",
                "context_length": 8192,
            },
            {
                "id": "mixtral-8x7b-32768",
                "context_length": 32768,
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        models = await provider.get_models(use_cache=False)

        assert len(models) == 2
        assert models[0].id == "llama3-70b-8192"
        assert models[1].context_length == 32768


@pytest.mark.asyncio
async def test_generic_provider_get_models_no_api_key():
    """Test GenericProvider raises ValueError when API key is not set"""
    import os

    original_key = os.environ.get("GROQ_API_KEY")

    try:
        if "GROQ_API_KEY" in os.environ:
            del os.environ["GROQ_API_KEY"]

        provider = get_provider("groq", api_key=None)

        with pytest.raises(ValueError, match="GROQ_API_KEY environment variable not set"):
            await provider.get_models()
    finally:
        if original_key:
            os.environ["GROQ_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_generic_provider_get_credits_no_api_key():
    """Test GenericProvider raises ValueError when API key is not set for credits"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        credits_endpoint="/credits",
    )

    with pytest.raises(ValueError, match="TEST_API_KEY environment variable not set"):
        await provider.get_credits()


@pytest.mark.asyncio
async def test_generic_provider_get_credits_no_endpoint():
    """Test GenericProvider returns None when credits_endpoint is not set"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
        credits_endpoint=None,
    )

    credits = await provider.get_credits()
    assert credits is None


@pytest.mark.asyncio
async def test_generic_provider_http_401_error():
    """Test GenericProvider handles 401 errors"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await provider.get_models(use_cache=False)


@pytest.mark.asyncio
async def test_generic_provider_http_429_error():
    """Test GenericProvider handles 429 errors"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await provider.get_models(use_cache=False)


@pytest.mark.asyncio
async def test_generic_provider_http_500_error():
    """Test GenericProvider handles 500 errors"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
    )

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(APIError, match="API request failed with status 500"):
            await provider.get_models(use_cache=False)


@pytest.mark.asyncio
async def test_generic_provider_network_error():
    """Test GenericProvider handles network errors"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.RequestError("Connection failed")

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(NetworkError, match="Network error occurred"):
            await provider.get_models(use_cache=False)


@pytest.mark.asyncio
async def test_generic_provider_credits_401_error():
    """Test GenericProvider handles 401 errors in credits"""
    provider = GenericProvider(
        provider_name="test",
        base_url="https://api.test.com",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        parser=OpenAICompatibleParser(model_path="data"),
        api_key="test_key",
        credits_endpoint="/credits",
    )

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await provider.get_credits()


def test_provider_factory_create_openai_compatible():
    """Test ProviderFactory.create_openai_compatible"""
    provider = ProviderFactory.create_openai_compatible(
        provider_name="test_provider",
        base_url="https://api.test.com/v1",
        api_key_env="TEST_API_KEY",
        models_endpoint="/models",
        credits_endpoint="/credits",
        api_key="test_key",
    )

    assert provider.provider_name == "test_provider"
    assert provider.base_url == "https://api.test.com/v1"
    assert provider.api_key_env == "TEST_API_KEY"
    assert provider.api_key == "test_key"
    assert provider.models_endpoint == "/models"
    assert provider.credits_endpoint == "/credits"


def test_provider_factory_create_openrouter():
    """Test ProviderFactory.create_openrouter"""
    provider = ProviderFactory.create_openrouter(api_key="test_key")

    assert provider.provider_name == "openrouter"
    assert provider.base_url == "https://openrouter.ai/api/v1"
    assert provider.api_key_env == "OPENROUTER_API_KEY"
    assert provider.api_key == "test_key"
    assert provider.models_endpoint == "/models"
    assert provider.credits_endpoint == "/credits"


def test_get_provider_unknown_provider():
    """Test get_provider raises ValueError for unknown provider"""
    with pytest.raises(ValueError, match="Unknown provider: nonexistent"):
        get_provider("nonexistent")


def test_get_provider_unknown_parser_type(monkeypatch):
    """Test _create_provider_from_config raises ValueError for unknown parser type"""
    # Temporarily modify the provider config to use an unknown parser
    monkeypatch.setenv("TEST_API_KEY", "test_key")

    from llminfo_cli.providers import _create_provider_from_config

    config = {
        "name": "test",
        "base_url": "https://api.test.com",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "unknown_parser",
    }

    with pytest.raises(ValueError, match="Unknown parser type: unknown_parser"):
        _create_provider_from_config("test", config)


def test_get_providers_returns_multiple():
    """Test get_providers returns all configured providers"""
    providers = get_providers()

    # Should return at least the built-in providers
    assert len(providers) > 0
    assert "openrouter" in providers
    assert "groq" in providers

    # Each provider should have the correct name
    for name, provider in providers.items():
        assert provider.provider_name == name
