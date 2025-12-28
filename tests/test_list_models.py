"""Tests for list models command"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llminfo_cli.providers import get_provider


@pytest.mark.asyncio
async def test_list_models_single_provider():
    """Test listing models from a single provider"""
    mock_response_data = {
        "data": [
            {
                "id": "llama3-70b-8192",
                "context_length": 8192,
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
        provider = get_provider("groq", api_key="test_key")
        models = await provider.get_models(use_cache=False)

        assert len(models) == 1
        assert models[0].id == "llama3-70b-8192"
        assert models[0].context_length == 8192


@pytest.mark.asyncio
async def test_list_models_all_providers():
    """Test that get_providers returns all configured providers"""
    from llminfo_cli.providers import get_providers

    providers = get_providers()

    assert "openrouter" in providers
    assert "groq" in providers
    assert "cerebras" in providers
    assert "mistral" in providers
