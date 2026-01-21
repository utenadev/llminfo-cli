"""Integration tests with actual API calls"""

import os

import pytest

from llminfo_cli.providers.openrouter import OpenRouterProvider
from llminfo_cli.providers import get_provider


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

    print(f"\nTotal models: {len(models)}")
    print("First 3 models:")
    for model in models[:3]:
        print(f"  - {model.id} ({model.name})")


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

    print(f"\nTotal credits: ${credits.total_credits:.2f}")
    print(f"Usage: ${credits.usage:.2f}")
    print(f"Remaining: ${credits.remaining:.2f}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_groq_get_models_real():
    """Test fetching models from actual Groq API"""
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        pytest.skip("GROQ_API_KEY not set in environment")

    provider = get_provider("groq", api_key=api_key)
    models = await provider.get_models()

    assert len(models) > 0

    print(f"\nTotal models: {len(models)}")
    print("First 3 models:")
    for model in models[:3]:
        print(f"  - {model.id}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_groq_get_credits_real():
    """Test that Groq provider returns None for credits (not supported)"""
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        pytest.skip("GROQ_API_KEY not set in environment")

    provider = get_provider("groq", api_key=api_key)
    credits = await provider.get_credits()

    assert credits is None

    print("\nGroq provider correctly returns None for credits (not supported)")


def test_provider_integration_with_mocks():
    """Test provider integration using mocks (no API calls)"""
    # This test verifies the integration flow without actual async calls
    # The actual async testing is done in unit tests with proper mocking

    # Test that providers can be instantiated correctly
    provider = OpenRouterProvider(api_key="test_key")
    assert provider.provider_name == "openrouter"
    assert provider.api_key == "test_key"


def test_provider_switching_integration():
    """Test switching between different providers"""
    # Test that different providers can be instantiated
    providers_to_test = ["openrouter", "groq", "cerebras", "mistral"]

    for provider_name in providers_to_test:
        provider = get_provider(provider_name, api_key="test_key")
        assert provider.provider_name == provider_name
