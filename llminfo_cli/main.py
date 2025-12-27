"""CLI entry point for llminfo"""

import asyncio
import json
import sys
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from llminfo_cli.models import select_best_free_model
from llminfo_cli.providers.openrouter import OpenRouterProvider
from llminfo_cli.schemas import ModelInfo

app = typer.Typer()
console = Console()


@app.callback()
def main(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """llminfo: CLI tool for LLM model information"""
    pass


def get_provider(provider_name: str, api_key: Optional[str] = None) -> OpenRouterProvider:
    """Get provider instance by name"""
    if provider_name == "openrouter":
        return OpenRouterProvider(api_key=api_key)
    else:
        typer.echo(f"Provider '{provider_name}' not yet implemented", err=True)
        sys.exit(1)


def format_models_table(models: list[ModelInfo]) -> Table:
    """Format models as a rich table"""
    table = Table(title="Available Models")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Context", style="yellow")
    table.add_column("Free", style="magenta")

    for model in models:
        context_str = f"{model.context_length:,}" if model.context_length else "N/A"
        free_str = "✓" if model.is_free else "✗"
        table.add_row(model.id, model.name, context_str, free_str)

    return table


@app.command()
def list_free(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List free models from the specified provider"""

    async def run():
        try:
            provider_instance = get_provider(provider)
            models = await provider_instance.get_models()
            free_models = [m for m in models if m.is_free]

            if json_output:
                output = {
                    "provider": provider,
                    "models": [m.model_dump() for m in free_models],
                }
                typer.echo(json.dumps(output, indent=2))
            else:
                if not free_models:
                    typer.echo("No free models available")
                else:
                    table = format_models_table(free_models)
                    console.print(table)

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


@app.command()
def best_free(
    provider: str = typer.Option("openrouter", "--provider", help="Provider name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Select and display the best free model"""

    async def run():
        try:
            provider_instance = get_provider(provider)
            models = await provider_instance.get_models()
            best_model = select_best_free_model(models)

            if json_output:
                typer.echo(json.dumps(best_model.model_dump(), indent=2))
            else:
                typer.echo(f"Best free model: {best_model.id}")
                typer.echo(f"Name: {best_model.name}")
                if best_model.context_length:
                    typer.echo(f"Context: {best_model.context_length:,}")
                if best_model.pricing:
                    typer.echo(f"Pricing: {best_model.pricing}")

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


if __name__ == "__main__":
    app()
