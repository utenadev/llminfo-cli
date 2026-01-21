"""Test configuration and shared fixtures"""

from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

runner = CliRunner()


def mock_provider_with_error(error=None):
    """Helper to create a mock provider with optional error side effect.

    Args:
        error: Exception to raise when get_models is called

    Returns:
        MagicMock: Configured mock provider
    """
    mock_provider = MagicMock()
    mock_provider.provider_name = "test"
    if error:
        mock_provider.get_models.side_effect = error
        mock_provider.get_credits.side_effect = error
    else:
        mock_model = MagicMock()
        mock_model.id = "model1"
        mock_model.name = "Model 1"
        mock_model.context_length = 1000
        mock_model.model_dump.return_value = {"id": "model1", "name": "Model 1"}
        mock_provider.get_models.return_value = [mock_model]
        mock_provider.get_credits.return_value = MagicMock(
            total_credits=100.0, usage=25.0, remaining=75.0
        )
    return mock_provider


def run_with_mocked_asyncio(test_func):
    """Helper to run a test function with mocked asyncio.run.

    This prevents actual async execution and suppresses coroutine warnings.

    Args:
        test_func: Function to execute with mocked asyncio
    """
    with patch("llminfo_cli.main.asyncio.run") as mock_asyncio_run:
        mock_asyncio_run.return_value = None
        return test_func(mock_asyncio_run)
