"""CLI entry point for llminfo"""

import asyncio
import json
import logging
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from llminfo_cli.providers import get_provider, get_providers
from llminfo_cli.providers.parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser
from llminfo_cli.providers.generic import GenericProvider
from llminfo_cli.schemas import ModelInfo
from llminfo_cli.errors import APIError, NetworkError
from llminfo_cli.validators import validate_provider_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("llminfo.log", mode="a")],
)
logger = logging.getLogger("llminfo")

app = typer.Typer()
list_app = typer.Typer(help="List models from providers")
app.add_typer(list_app, name="list")
console = Console()


def async_command(func: Callable) -> Callable:
    """Decorator to run async functions in Typer commands."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        asyncio.run(func(*args, **kwargs))

    return wrapper


def handle_command_error(error: Exception, command_name: str) -> None:
    """Handle errors from CLI commands with consistent output.

    Args:
        error: The exception that occurred
        command_name: Name of the command for logging
    """
    if isinstance(error, ValueError):
        logger.error(f"{command_name} failed: {error}")
        typer.echo(f"Value error: {error}", err=True)
        typer.echo("\nRun 'llminfo --help' to see available commands.", err=True)
    elif isinstance(error, APIError):
        logger.error(f"API error in {command_name}: {error.status_code}")

        # Provide more specific error messages based on status code
        if error.status_code == 401:
            typer.echo("Authentication failed: Invalid or missing API key.", err=True)
            typer.echo("Please check your API key configuration.", err=True)
            if hasattr(error, 'provider') and error.provider:
                typer.echo(f"Provider: {error.provider}", err=True)
                typer.echo(f"Make sure the environment variable for {error.provider.upper()}_API_KEY is set correctly.", err=True)
        elif error.status_code == 429:
            typer.echo("Rate limit exceeded: Too many requests.", err=True)
            typer.echo("Please wait before making more requests.", err=True)
        elif error.status_code == 404:
            typer.echo("Resource not found: The requested resource does not exist.", err=True)
        elif error.status_code is not None and error.status_code >= 500:
            typer.echo(f"Server error ({error.status_code}): The provider's server encountered an error.", err=True)
            typer.echo("Please try again later.", err=True)
        else:
            error_msg = f"API error ({error.status_code}): {str(error)}" if error.status_code is not None else f"API error: {str(error)}"
            typer.echo(error_msg, err=True)
    elif isinstance(error, NetworkError):
        logger.error(f"Network error in {command_name}: {error}")
        typer.echo(f"Network error: {error}", err=True)
        typer.echo("Please check your internet connection and firewall settings.", err=True)
    else:
        logger.error(f"Error in {command_name}: {error}")
        typer.echo(f"Unexpected error: {error}", err=True)
        typer.echo("Please check the log file 'llminfo.log' for more details.", err=True)
    sys.exit(1)


def load_and_validate_config(config_file: Path) -> dict[str, Any]:
    """Load and validate provider configuration from YAML file.

    Args:
        config_file: Path to the YAML configuration file

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If file not found or validation fails
    """
    if not config_file.exists():
        raise ValueError(f"Plugin file not found: {config_file}")

    with config_file.open() as f:
        config: dict[str, Any] = yaml.safe_load(f)

    is_valid, error = validate_provider_config(config)
    if not is_valid:
        raise ValueError(f"Configuration error: {error}")

    return config


def create_provider_from_config(
    config: dict[str, str], api_key: Optional[str] = None
) -> GenericProvider:
    """Create provider instance from configuration.

    Args:
        config: Provider configuration dictionary
        api_key: Optional API key to override environment variable

    Returns:
        Configured GenericProvider instance
    """
    parser_type = config.get("parser", "openai_compatible")

    parser: ResponseParser
    if parser_type == "openai_compatible":
        parser = OpenAICompatibleParser(model_path="data")
    elif parser_type == "openrouter":
        parser = OpenRouterParser()
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")

    return GenericProvider(
        provider_name=config["name"],
        base_url=config["base_url"],
        api_key_env=config["api_key_env"],
        models_endpoint=config["models_endpoint"],
        parser=parser,
        credits_endpoint=config.get("credits_endpoint"),
        api_key=api_key,
    )


def format_models_table(models: list[tuple[str, ModelInfo]]) -> Table:
    """Format models as a rich table.

    Args:
        models: List of (provider_name, ModelInfo) tuples

    Returns:
        Configured Rich Table
    """
    table = Table(title="Available Models")
    table.add_column("Provider", style="magenta")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Context", style="yellow")

    for provider_name, model in models:
        context_str = f"{model.context_length:,}" if model.context_length else "N/A"
        table.add_row(provider_name, model.id, model.name, context_str)

    return table


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """llminfo: CLI tool for LLM model information"""
    logger.info("llminfo CLI started")
    if ctx.invoked_subcommand is None:
        logger.info("Displaying help message")
        typer.echo("Usage: llminfo [COMMAND] [OPTIONS]")
        typer.echo("\nAvailable commands:")
        typer.echo("  credits         Display credit balance for the specified provider")
        typer.echo("  list            List models from providers")
        typer.echo("  test-provider   Test a provider configuration")
        typer.echo("  import-provider Test and import a provider configuration")
        typer.echo("\nRun 'llminfo [COMMAND] --help' for command-specific help.")
        typer.echo("\nExamples:")
        typer.echo("  llminfo list models                    # List all models")
        typer.echo("  llminfo credits --provider openrouter  # Check credits")
        raise typer.Exit()


@app.command()
@async_command
async def credits(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Display credit balance for the specified provider

    Examples:
      llminfo credits --provider openrouter  # Check OpenRouter credits
      llminfo credits --json               # Output in JSON format
    """
    try:
        logger.info(f"Checking credits for provider: {provider}")
        provider_instance = get_provider(provider)
        credits_info = await provider_instance.get_credits()

        if credits_info is None:
            typer.echo("Credits not available for this provider", err=True)
            return  # Return instead of exiting with error code

        if json_output:
            typer.echo(json.dumps(credits_info.model_dump(), indent=2))
        else:
            typer.echo(f"Total Credits: ${credits_info.total_credits:.2f}")
            typer.echo(f"Usage: ${credits_info.usage:.2f}")
            typer.echo(f"Remaining: ${credits_info.remaining:.2f}")

    except Exception as e:
        handle_command_error(e, "credits command")


@list_app.command()
@async_command
async def models(
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    force: bool = typer.Option(False, "--force", help="Force refresh from API (ignore cache)"),
):
    """
    List models from all or specified providers

    Examples:
      llminfo list models                    # List models from all providers
      llminfo list models --provider openrouter  # List models from OpenRouter only
      llminfo list models --json             # Output in JSON format
      llminfo list models --force            # Force refresh from API
    """
    try:
        logger.info(f"Listing models, provider: {provider or 'all'}, force: {force}")

        if provider:
            provider_instance = get_provider(provider)
            models = await provider_instance.get_models(use_cache=not force)
            models_with_provider = [(provider_instance.provider_name, m) for m in models]
            logger.info(f"Retrieved {len(models)} models from {provider}")
        else:
            providers = get_providers()
            models_with_provider = []
            for provider_name, provider_instance in providers.items():
                models = await provider_instance.get_models(use_cache=not force)
                models_with_provider.extend([(provider_instance.provider_name, m) for m in models])
                logger.info(f"Retrieved {len(models)} models from {provider_name}")

        logger.info(f"Total models retrieved: {len(models_with_provider)}")

        if json_output:
            output = [{"provider": pn, "model": m.model_dump()} for pn, m in models_with_provider]
            typer.echo(json.dumps(output, indent=2))
        elif not models_with_provider:
            typer.echo("No models available")
        else:
            table = format_models_table(models_with_provider)
            console.print(table)

    except Exception as e:
        handle_command_error(e, "list models command")


def display_test_results(models: list, config: dict[str, Any]) -> None:
    """Display provider test results to user.

    Args:
        models: List of models retrieved
        config: Provider configuration dictionary
    """
    typer.echo(f"Testing provider: {config['name']}")
    typer.echo(f"Base URL: {config['base_url']}")
    typer.echo(f"✓ Successfully retrieved {len(models)} models")

    if models:
        typer.echo("\nFirst few models:")
        for model in models[:3]:
            typer.echo(f"  - {model.id}")


@app.command()
@async_command
async def test_provider(
    plugin_file: Path = typer.Argument(..., help="Path to plugin YAML file"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for testing"),
):
    """
    Test a provider configuration without adding it to providers.yml

    Examples:
      llminfo test-provider plugin/new-provider.yml  # Test with API key from env
      llminfo test-provider plugin/new-provider.yml --api-key your-key  # Test with specific key
    """
    try:
        logger.info(f"Testing provider configuration: {plugin_file}")
        config = load_and_validate_config(plugin_file)
        provider = create_provider_from_config(config, api_key=api_key)

        models = await provider.get_models(use_cache=False)
        logger.info(f"Successfully tested provider {config['name']}: {len(models)} models")

        display_test_results(models, config)

    except Exception as e:
        handle_command_error(e, "test provider command")


@app.command()
@async_command
async def import_provider(
    plugin_file: Path = typer.Argument(..., help="Path to plugin YAML file"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for testing"),
):
    """
    Test and import a provider configuration into providers.yml

    Examples:
      llminfo import-provider plugin/new-provider.yml  # Import with API key from env
      llminfo import-provider plugin/new-provider.yml --api-key your-key  # Import with specific key
    """
    try:
        logger.info(f"Importing provider configuration: {plugin_file}")
        config = load_and_validate_config(plugin_file)
        provider_name = config["name"]

        provider = create_provider_from_config(config, api_key=api_key)
        models = await provider.get_models(use_cache=False)
        logger.info(f"Successfully imported provider {provider_name}: {len(models)} models")

        display_test_results(models, config)

        typer.echo(f"\nAdding {provider_name} to user providers.yml...")

        config_dir = Path.home() / ".config" / "llminfo"
        config_dir.mkdir(parents=True, exist_ok=True)
        user_providers_yml = config_dir / "providers.yml"

        if user_providers_yml.exists():
            with user_providers_yml.open() as f:
                user_config = yaml.safe_load(f) or {}
        else:
            user_config = {"providers": {}}

        user_config.setdefault("providers", {})[provider_name] = config

        with user_providers_yml.open("w") as f:
            yaml.dump(user_config, f, default_flow_style=False)

        typer.echo(f"✓ Provider '{provider_name}' successfully added to user providers.yml")
        typer.echo(f"Plugin file can be deleted: {plugin_file}")

    except Exception as e:
        handle_command_error(e, "import provider command")


if __name__ == "__main__":
    app()
