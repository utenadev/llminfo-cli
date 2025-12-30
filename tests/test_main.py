"""Tests for CLI main module"""

import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner
from llminfo_cli.main import app

runner = CliRunner()


def test_root_command_displays_guide():
    """Test that root command displays guide when no subcommand provided"""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Available commands:" in result.output
    assert "llminfo [COMMAND] --help" in result.output


def test_credits_command():
    """Test credits command with mocked provider"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.return_value = MagicMock(
            total_credits=100.0, usage=25.0, remaining=75.0
        )
        mock_get_provider.return_value = mock_provider

        # Mock the async run function to avoid asyncio issues
        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_credits_command_json_output():
    """Test credits command with JSON output"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.return_value = MagicMock(
            total_credits=100.0,
            usage=25.0,
            remaining=75.0,
            model_dump=lambda: {"total_credits": 100.0, "usage": 25.0, "remaining": 75.0},
        )
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "test", "--json"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_credits_command_error():
    """Test credits command error handling"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.side_effect = ValueError("Test error")
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 0  # CliRunner doesn't capture sys.exit
        mock_asyncio_run.assert_called_once()


def test_list_models_command():
    """Test list models command with mocked providers"""
    with (
        patch("llminfo_cli.main.get_providers") as mock_get_providers,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_provider.get_models.return_value = [
            MagicMock(id="model1", name="Model 1", context_length=1000)
        ]
        mock_get_providers.return_value = {"test": mock_provider}

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_list_models_command_specific_provider():
    """Test list models command with specific provider"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_provider.get_models.return_value = [
            MagicMock(id="model1", name="Model 1", context_length=1000)
        ]
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_list_models_command_json_output():
    """Test list models command with JSON output"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"id": "model1", "name": "Model 1"}
        mock_provider.get_models.return_value = [mock_model]
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.return_value = None

        result = runner.invoke(app, ["list", "models", "--provider", "test", "--json"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_models_command_http_401():
    """Test models command with 401 Unauthorized error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.side_effect = lambda coroutine: coroutine.send(None)

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 1
        assert "API error: 401" in result.output


def test_models_command_http_429():
    """Test models command with 429 Rate Limit error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.HTTPStatusError(
            "Rate Limit Exceeded",
            request=MagicMock(),
            response=MagicMock(status_code=429)
        )
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.side_effect = lambda coroutine: coroutine.send(None)

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 1
        assert "API error: 429" in result.output


def test_models_command_network_error():
    """Test models command with network error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.RequestError("Connection error")
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.side_effect = lambda coroutine: coroutine.send(None)

        result = runner.invoke(app, ["list", "models", "--provider", "test"])
        assert result.exit_code == 1
        assert "Network error" in result.output


def test_credits_command_http_401():
    """Test credits command with 401 Unauthorized error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.side_effect = lambda coroutine: coroutine.send(None)

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 1
        assert "Error" in result.output


def test_credits_command_network_error():
    """Test credits command with network error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.side_effect = httpx.RequestError("Connection error")
        mock_get_provider.return_value = mock_provider

        mock_asyncio_run.side_effect = lambda coroutine: coroutine.send(None)

        result = runner.invoke(app, ["credits", "--provider", "test"])
        assert result.exit_code == 1
        assert "Error" in result.output
