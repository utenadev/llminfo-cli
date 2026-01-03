"""CLI entry point for llminfo"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from llminfo_cli.providers import get_provider, get_providers
from llminfo_cli.providers.parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser
from llminfo_cli.providers.generic import GenericProvider
from llminfo_cli.validators import validate_provider_config
from llminfo_cli.schemas import ModelInfo
from llminfo_cli.errors import APIError, NetworkError, AuthenticationError, RateLimitError

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


def format_models_table(models: list[tuple[str, ModelInfo]]) -> Table:
    """Format models as a rich table"""
    table = Table(title="Available Models")
    table.add_column("Provider", style="magenta")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Context", style="yellow")

    for provider_name, model in models:
        context_str = f"{model.context_length:,}" if model.context_length else "N/A"
        table.add_row(provider_name, model.id, model.name, context_str)

    return table


@app.command()
def credits(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Display credit balance for the specified provider

    Examples:
      llminfo credits --provider openrouter  # Check OpenRouter credits
      llminfo credits --json               # Output in JSON format
    """

    async def run():
        logger.info(f"Checking credits for provider: {provider}")
        try:
            provider_instance = get_provider(provider)
            credits_info = await provider_instance.get_credits()

            if credits_info is None:
                typer.echo("Credits not available for this provider", err=True)
                sys.exit(1)

            if json_output:
                typer.echo(json.dumps(credits_info.model_dump(), indent=2))
            else:
                typer.echo(f"Total Credits: ${credits_info.total_credits:.2f}")
                typer.echo(f"Usage: ${credits_info.usage:.2f}")
                typer.echo(f"Remaining: ${credits_info.remaining:.2f}")

        except ValueError as e:
            logger.error(f"Credits command failed: {e}")
            typer.echo(str(e), err=True)
            typer.echo("\nRun 'llminfo --help' to see available commands.", err=True)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error in credits command: {e}")
            typer.echo(f"Error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


@list_app.command()
def models(
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

    async def run():
        logger.info(f"Listing models, provider: {provider or 'all'}, force: {force}")
        try:
            if provider:
                provider_instance = get_provider(provider)
                models = await provider_instance.get_models(use_cache=not force)
                models_with_provider = [(provider_instance.provider_name, m) for m in models]
                logger.info(f"Retrieved {len(models)} models from {provider}")
            else:
                providers = get_providers()
                all_models = []
                for provider_name, provider_instance in providers.items():
                    models = await provider_instance.get_models(use_cache=not force)
                    all_models.extend([(provider_instance.provider_name, m) for m in models])
                    logger.info(f"Retrieved {len(models)} models from {provider_name}")
                models_with_provider = all_models
            logger.info(f"Total models retrieved: {len(all_models)}")

            if json_output:
                output = [
                    {"provider": pn, "model": m.model_dump()} for pn, m in models_with_provider
                ]
                typer.echo(json.dumps(output, indent=2))
            else:
                if not models_with_provider:
                    typer.echo("No models available")
                else:
                    table = format_models_table(models_with_provider)
                    console.print(table)

        except ValueError as e:
            logger.error(f"List models command failed: {e}")
            typer.echo(str(e), err=True)
            typer.echo("\nRun 'llminfo --help' to see available commands.", err=True)
            sys.exit(1)
        except APIError as e:
            logger.error(f"API error in list models command: {e.status_code}")
            typer.echo(f"API error: {e.status_code}", err=True)
            sys.exit(1)
        except NetworkError as e:
            logger.error(f"Network error in list models command: {e}")
            typer.echo(f"Network error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


def _create_provider_from_config(
    config: Dict[str, str], api_key: str | None = None
) -> GenericProvider:
    """Create provider instance from configuration"""
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


@app.command()
def test_provider(
    plugin_file: Path = typer.Argument(..., help="Path to plugin YAML file"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for testing"),
):
    """
    Test a provider configuration without adding it to providers.yml

    Examples:
      llminfo test-provider plugin/new-provider.yml  # Test with API key from env
      llminfo test-provider plugin/new-provider.yml --api-key your-key  # Test with specific key
    """

    async def run():
        logger.info(f"Testing provider configuration: {plugin_file}")
        try:
            if not plugin_file.exists():
                logger.error(f"Plugin file not found: {plugin_file}")
                typer.echo(f"Plugin file not found: {plugin_file}", err=True)
                sys.exit(1)

            with plugin_file.open() as f:
                config = yaml.safe_load(f)

            is_valid, error = validate_provider_config(config)
            if not is_valid:
                logger.error(f"Configuration validation failed: {error}")
                typer.echo(f"Configuration error: {error}", err=True)
                sys.exit(1)

            provider = _create_provider_from_config(config, api_key=api_key)

            typer.echo(f"Testing provider: {config['name']}")
            typer.echo(f"Base URL: {config['base_url']}")

            models = await provider.get_models(use_cache=False)
            logger.info(f"Successfully tested provider {config['name']}: {len(models)} models")

            typer.echo(f"✓ Successfully retrieved {len(models)} models")

            if models:
                typer.echo("\nFirst few models:")
                for model in models[:3]:
                    typer.echo(f"  - {model.id}")

        except ValueError as e:
            logger.error(f"Test provider command failed: {e}")
            typer.echo(f"Configuration error: {e}", err=True)
            typer.echo("\nRun 'llminfo --help' to see available commands.", err=True)
            sys.exit(1)
        except APIError as e:
            logger.error(f"API error in test provider command: {e.status_code}")
            typer.echo(f"API error: {e.status_code}", err=True)
            sys.exit(1)
        except NetworkError as e:
            logger.error(f"Network error in test provider command: {e}")
            typer.echo(f"Network error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


@app.command()
def import_provider(
    plugin_file: Path = typer.Argument(..., help="Path to plugin YAML file"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for testing"),
):
    """
    Test and import a provider configuration into providers.yml

    Examples:
      llminfo import-provider plugin/new-provider.yml  # Import with API key from env
      llminfo import-provider plugin/new-provider.yml --api-key your-key  # Import with specific key
    """

    async def run():
        logger.info(f"Importing provider configuration: {plugin_file}")
        try:
            if not plugin_file.exists():
                logger.error(f"Plugin file not found: {plugin_file}")
                typer.echo(f"Plugin file not found: {plugin_file}", err=True)
                sys.exit(1)

            with plugin_file.open() as f:
                config = yaml.safe_load(f)

            is_valid, error = validate_provider_config(config)
            if not is_valid:
                logger.error(f"Configuration validation failed: {error}")
                typer.echo(f"Configuration error: {error}", err=True)
                sys.exit(1)

            provider_name = config["name"]

            typer.echo(f"Testing provider: {provider_name}")
            typer.echo(f"Base URL: {config['base_url']}")

            provider = _create_provider_from_config(config, api_key=api_key)

            models = await provider.get_models(use_cache=False)
            logger.info(f"Successfully imported provider {provider_name}: {len(models)} models")

            typer.echo(f"✓ Successfully retrieved {len(models)} models")

            if models:
                typer.echo("\nFirst few models:")
                for model in models[:3]:
                    typer.echo(f"  - {model.id}")

            typer.echo(f"\nAdding {provider_name} to user providers.yml...")

            # Create user config directory if it doesn't exist
            config_dir = Path.home() / ".config" / "llminfo"
            config_dir.mkdir(parents=True, exist_ok=True)

            user_providers_yml = config_dir / "providers.yml"

            # Load existing user config or create new one
            if user_providers_yml.exists():
                with user_providers_yml.open() as f:
                    user_providers_config = yaml.safe_load(f) or {}
            else:
                user_providers_config = {"providers": {}}

            # Add the new provider
            user_providers_config.setdefault("providers", {})[provider_name] = config

            # Write back to user config file
            with user_providers_yml.open("w") as f:
                yaml.dump(user_providers_config, f, default_flow_style=False)

            typer.echo(f"✓ Provider '{provider_name}' successfully added to user providers.yml")
            typer.echo(f"Plugin file can be deleted: {plugin_file}")

        except ValueError as e:
            logger.error(f"Import provider command failed: {e}")
            typer.echo(f"Configuration error: {e}", err=True)
            typer.echo("\nRun 'llminfo --help' to see available commands.", err=True)
            sys.exit(1)
        except APIError as e:
            logger.error(f"API error in import provider command: {e.status_code}")
            typer.echo(f"API error: {e.status_code}", err=True)
            sys.exit(1)
        except NetworkError as e:
            logger.error(f"Network error in import provider command: {e}")
            typer.echo(f"Network error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


if __name__ == "__main__":
    app()
