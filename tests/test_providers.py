"""Tests for provider implementations"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llminfo_cli.providers.openrouter import OpenRouterProvider


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
        assert models[0].is_free is True
        assert models[1].context_length == 1000000


@pytest.mark.asyncio
async def test_openrouter_get_models_no_api_key():
    """Test error when API key is not set"""
    provider = OpenRouterProvider(api_key=None)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable not set"):
        await provider.get_models()


@pytest.mark.asyncio
async def test_openrouter_get_credits():
    """Test fetching credits from OpenRouter"""
    provider = OpenRouterProvider(api_key="test_key")

    mock_response_data = {
        "data": {
            "total_credits": 100.0,
            "usage": 25.5,
            "remaining": 74.5,
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

        assert credits.total_credits == 100.0
        assert credits.usage == 25.5
        assert credits.remaining == 74.5


def test_provider_name():
    """Test provider name property"""
    provider = OpenRouterProvider(api_key="test_key")
    assert provider.provider_name == "openrouter"
