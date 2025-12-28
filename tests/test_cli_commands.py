"""Tests for CLI commands (test-provider, import-provider)"""

import pytest  # noqa: F401
from llminfo_cli.validators import validate_provider_config


def test_validate_valid_config():
    """Test validation of valid provider configuration"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
        "credits_endpoint": None,
    }

    is_valid, error = validate_provider_config(config)

    assert is_valid
    assert error == ""


def test_validate_missing_required_field():
    """Test validation fails with missing required field"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Missing required field" in error


def test_validate_invalid_base_url():
    """Test validation fails with invalid base_url"""
    config = {
        "name": "test_provider",
        "base_url": "not-a-valid-url",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
        "credits_endpoint": None,
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "must start with" in error


def test_validate_invalid_parser():
    """Test validation fails with invalid parser"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "invalid_parser",
        "credits_endpoint": None,
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid parser" in error


def test_validate_invalid_api_key_env_case():
    """Test validation fails with lowercase api_key_env"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "test_api_key",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
        "credits_endpoint": None,
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "should be uppercase" in error
