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


def test_validate_empty_name():
    """Test validation fails with empty name"""
    config = {
        "name": "",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'name'" in error


def test_validate_non_string_name():
    """Test validation fails with non-string name"""
    config = {
        "name": 123,
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'name'" in error


def test_validate_empty_base_url():
    """Test validation fails with empty base_url"""
    config = {
        "name": "test_provider",
        "base_url": "",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'base_url'" in error


def test_validate_non_string_base_url():
    """Test validation fails with non-string base_url"""
    config = {
        "name": "test_provider",
        "base_url": 123,
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'base_url'" in error


def test_validate_empty_api_key_env():
    """Test validation fails with empty api_key_env"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'api_key_env'" in error


def test_validate_non_string_api_key_env():
    """Test validation fails with non-string api_key_env"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": 123,
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'api_key_env'" in error


def test_validate_empty_models_endpoint():
    """Test validation fails with empty models_endpoint"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "",
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'models_endpoint'" in error


def test_validate_non_string_models_endpoint():
    """Test validation fails with non-string models_endpoint"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": 123,
        "parser": "openai_compatible",
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid or missing 'models_endpoint'" in error


def test_validate_invalid_credits_endpoint_type():
    """Test validation fails with non-string credits_endpoint"""
    config = {
        "name": "test_provider",
        "base_url": "https://api.test.com/v1",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
        "credits_endpoint": 123,
    }

    is_valid, error = validate_provider_config(config)

    assert not is_valid
    assert "Invalid 'credits_endpoint'" in error
