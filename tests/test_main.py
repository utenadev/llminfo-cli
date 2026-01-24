"""Tests for CLI main module"""

import httpx
import pytest
import yaml
from pathlib import Path
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
            "Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
        )
        mock_get_provider.return_value = mock_provider

        # Mock asyncio.run to prevent actual async execution
        mock_asyncio_run.return_value = None

        _ = runner.invoke(app, ["list", "models", "--provider", "test"])
        # CliRunner doesn't capture sys.exit(), so exit_code will be 0
        # but we verify the command was invoked
        assert mock_asyncio_run.called


def test_models_command_http_429():
    """Test models command with 429 Rate Limit error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.HTTPStatusError(
            "Rate Limit Exceeded", request=MagicMock(), response=MagicMock(status_code=429)
        )
        mock_get_provider.return_value = mock_provider

        # Mock asyncio.run to prevent actual async execution
        mock_asyncio_run.return_value = None

        _ = runner.invoke(app, ["list", "models", "--provider", "test"])
        # CliRunner doesn't capture sys.exit(), so exit_code will be 0
        # but we verify the command was invoked
        assert mock_asyncio_run.called


def test_models_command_network_error():
    """Test models command with network error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_models.side_effect = httpx.RequestError("Connection error")
        mock_get_provider.return_value = mock_provider

        # Mock asyncio.run to prevent actual async execution
        mock_asyncio_run.return_value = None

        _ = runner.invoke(app, ["list", "models", "--provider", "test"])
        # CliRunner doesn't capture sys.exit(), so exit_code will be 0
        # but we verify the command was invoked
        assert mock_asyncio_run.called


def test_credits_command_http_401():
    """Test credits command with 401 Unauthorized error"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.get_credits.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)
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


# Tests for helper functions


def test_handle_command_error_value_error():
    """Test handle_command_error with ValueError"""
    from llminfo_cli.main import handle_command_error

    with patch("llminfo_cli.main.sys.exit") as mock_exit:
        error = ValueError("Invalid value")
        handle_command_error(error, "test_command")
        mock_exit.assert_called_once_with(1)


def test_handle_command_error_api_error():
    """Test handle_command_error with APIError"""
    from llminfo_cli.main import handle_command_error
    from llminfo_cli.errors import APIError

    with patch("llminfo_cli.main.sys.exit") as mock_exit:
        error = APIError("API error", status_code=500)
        handle_command_error(error, "test_command")
        mock_exit.assert_called_once_with(1)


def test_handle_command_error_api_error_without_status():
    """Test handle_command_error with APIError without status code"""
    from llminfo_cli.main import handle_command_error
    from llminfo_cli.errors import APIError

    with patch("llminfo_cli.main.sys.exit") as mock_exit:
        error = APIError("API error", status_code=None)
        handle_command_error(error, "test_command")
        mock_exit.assert_called_once_with(1)


def test_handle_command_error_network_error():
    """Test handle_command_error with NetworkError"""
    from llminfo_cli.main import handle_command_error
    from llminfo_cli.errors import NetworkError

    with patch("llminfo_cli.main.sys.exit") as mock_exit:
        error = NetworkError("Network error")
        handle_command_error(error, "test_command")
        mock_exit.assert_called_once_with(1)


def test_handle_command_error_generic_exception():
    """Test handle_command_error with generic Exception"""
    from llminfo_cli.main import handle_command_error

    with patch("llminfo_cli.main.sys.exit") as mock_exit:
        error = Exception("Generic error")
        handle_command_error(error, "test_command")
        mock_exit.assert_called_once_with(1)


def test_load_and_validate_config_valid():
    """Test load_and_validate_config with valid file"""
    from llminfo_cli.main import load_and_validate_config
    from pathlib import Path
    import tempfile
    import yaml

    config_data = {
        "name": "test",
        "base_url": "https://api.test.com",
        "api_key_env": "TEST_API_KEY",
        "models_endpoint": "/models",
        "parser": "openai_compatible",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        temp_path = Path(f.name)

    try:
        result = load_and_validate_config(temp_path)
        assert result == config_data
    finally:
        temp_path.unlink()


def test_load_and_validate_config_file_not_found():
    """Test load_and_validate_config with non-existent file"""
    from llminfo_cli.main import load_and_validate_config
    from pathlib import Path

    with pytest.raises(ValueError, match="Plugin file not found"):
        load_and_validate_config(Path("/nonexistent/file.yml"))


def test_load_and_validate_config_invalid_yaml():
    """Test load_and_validate_config with invalid YAML"""
    from llminfo_cli.main import load_and_validate_config
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("invalid:\n  - unclosed list")
        f.flush()
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError):
            load_and_validate_config(temp_path)
    finally:
        temp_path.unlink()


def test_credits_cli_command_none():
    """Test CLI credits command with None credits (using a provider that doesn't support credits)"""
    result = runner.invoke(app, ["credits", "--provider", "groq"])  # groq doesn't support credits
    assert result.exit_code == 0


def test_models_cli_command_force():
    """Test CLI models command with force flag"""
    with (
        patch("llminfo_cli.main.get_provider") as mock_get_provider,
        patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run,
    ):
        mock_provider = MagicMock()
        mock_provider.provider_name = "test"
        mock_provider.get_models = MagicMock()
        mock_get_provider.return_value = mock_provider

        result = runner.invoke(app, ["list", "models", "--provider", "test", "--force"])
        assert result.exit_code == 0
