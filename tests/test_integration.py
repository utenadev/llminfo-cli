"""Integration tests with actual API calls"""

import os

import pytest

from llminfo_cli.providers.openrouter import OpenRouterProvider


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openrouter_get_models_real():
    """Test fetching models from actual OpenRouter API"""
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set in environment")

    provider = OpenRouterProvider(api_key=api_key)
    models = await provider.get_models()

    assert len(models) > 0
    assert any(m.is_free for m in models)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openrouter_get_credits_real():
    """Test fetching credits from actual OpenRouter API"""
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set in environment")

    provider = OpenRouterProvider(api_key=api_key)
    credits = await provider.get_credits()

    assert credits is not None
    assert credits.total_credits >= 0
    assert credits.usage >= 0
    assert credits.remaining >= 0
