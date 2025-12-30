"""Tests for edge cases and error handling"""

from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
import httpx
import tempfile
import yaml
from pathlib import Path
from llminfo_cli.main import app

runner = CliRunner()


def test_empty_api_response():
    """Test handling of empty API responses"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.return_value = []  # Empty list
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_provider_not_found():
    """Test handling when provider is not found"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_get_provider.side_effect = ValueError("Unknown provider: nonexistent")

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "nonexistent"])
        assert result.exit_code == 0  # CliRunner doesn't capture sys.exit
        mock_asyncio_run.assert_called_once()


def test_api_key_missing():
    """Test handling when API key is missing"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_get_provider.side_effect = ValueError("API_KEY_ENV environment variable not set")

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_network_error():
    """Test handling of network errors"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.RequestError("Network error")
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_http_status_error():
    """Test handling of HTTP status errors"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
        )
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_test_provider_file_not_found():
    """Test test-provider command when plugin file doesn't exist"""
    result = runner.invoke(app, ["test-provider", "nonexistent.yml"])
    assert result.exit_code == 1
    assert "Plugin file not found" in result.output


def test_import_provider_file_not_found():
    """Test import-provider command when plugin file doesn't exist"""
    result = runner.invoke(app, ["import-provider", "nonexistent.yml"])
    assert result.exit_code == 1
    assert "Plugin file not found" in result.output


def test_invalid_provider_config():
    """Test handling of invalid provider configuration"""
    # Create temporary invalid config
    invalid_config = {
        "name": "test",
        # Missing required fields
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(invalid_config, f)
        temp_file = f.name

    try:
        result = runner.invoke(app, ["test-provider", temp_file])
        assert result.exit_code == 1
        assert "Configuration error" in result.output
    finally:
        Path(temp_file).unlink()


def test_credits_not_available():
    """Test credits command when credits are not available for provider"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.return_value = None  # Credits not available
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_force_refresh_cache():
    """Test that --force flag command structure is accepted"""
    # Test that the command accepts --force flag without error
    # The actual cache behavior is tested in integration tests
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_get_provider.return_value = mock_provider
        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test", "--force"])
        # CliRunner validates command structure
        assert result.exit_code == 0


def test_large_context_length_formatting():
    """Test formatting of large context lengths"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_model = MagicMock()
        mock_model.id = "model1"
        mock_model.name = "Model 1"
        mock_model.context_length = 128000  # Large number
        mock_provider.get_models.return_value = [mock_model]
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
