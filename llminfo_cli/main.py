"""CLI entry point for llminfo"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from llminfo_cli.providers import get_provider
from llminfo_cli.providers.parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser
from llminfo_cli.providers.generic import GenericProvider
from llminfo_cli.schemas import ModelInfo

app = typer.Typer()
console = Console()


@app.callback()
def main(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """llminfo: CLI tool for LLM model information"""
    pass


def format_models_table(models: list[ModelInfo]) -> Table:
    """Format models as a rich table"""
    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Context", style="yellow")

    for model in models:
        context_str = f"{model.context_length:,}" if model.context_length else "N/A"
        table.add_row(model.id, model.name, context_str)

    return table


@app.command()
def credits(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display credit balance for the specified provider"""

    async def run():
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
            typer.echo(str(e), err=True)
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            typer.echo(f"API error: {e.response.status_code}", err=True)
            sys.exit(1)
        except httpx.RequestError as e:
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
    """Test a provider configuration without adding it to providers.yml"""

    async def run():
        try:
            if not plugin_file.exists():
                typer.echo(f"Plugin file not found: {plugin_file}", err=True)
                sys.exit(1)

            with plugin_file.open() as f:
                config = yaml.safe_load(f)

            provider = _create_provider_from_config(config, api_key=api_key)

            typer.echo(f"Testing provider: {config['name']}")
            typer.echo(f"Base URL: {config['base_url']}")

            models = await provider.get_models()

            typer.echo(f"✓ Successfully retrieved {len(models)} models")

            if models:
                typer.echo("\nFirst few models:")
                for model in models[:3]:
                    typer.echo(f"  - {model.id}")

        except ValueError as e:
            typer.echo(f"Configuration error: {e}", err=True)
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            typer.echo(f"API error: {e.response.status_code}", err=True)
            sys.exit(1)
        except httpx.RequestError as e:
            typer.echo(f"Network error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


@app.command()
def import_provider(
    plugin_file: Path = typer.Argument(..., help="Path to plugin YAML file"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for testing"),
):
    """Test and import a provider configuration into providers.yml"""

    async def run():
        try:
            if not plugin_file.exists():
                typer.echo(f"Plugin file not found: {plugin_file}", err=True)
                sys.exit(1)

            with plugin_file.open() as f:
                config = yaml.safe_load(f)

            provider_name = config["name"]

            typer.echo(f"Testing provider: {provider_name}")
            typer.echo(f"Base URL: {config['base_url']}")

            provider = _create_provider_from_config(config, api_key=api_key)

            models = await provider.get_models()

            typer.echo(f"✓ Successfully retrieved {len(models)} models")

            if models:
                typer.echo("\nFirst few models:")
                for model in models[:3]:
                    typer.echo(f"  - {model.id}")

            typer.echo(f"\nAdding {provider_name} to providers.yml...")

            providers_yml = Path(__file__).parent.parent / "providers.yml"

            with providers_yml.open() as f:
                providers_config = yaml.safe_load(f)

            providers_config["providers"][provider_name] = config

            with providers_yml.open("w") as f:
                yaml.dump(providers_config, f, default_flow_style=False)

            typer.echo(f"✓ Provider '{provider_name}' successfully added to providers.yml")
            typer.echo(f"Plugin file can be deleted: {plugin_file}")

        except ValueError as e:
            typer.echo(f"Configuration error: {e}", err=True)
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            typer.echo(f"API error: {e.response.status_code}", err=True)
            sys.exit(1)
        except httpx.RequestError as e:
            typer.echo(f"Network error: {e}", err=True)
            sys.exit(1)

    asyncio.run(run())


if __name__ == "__main__":
    app()
