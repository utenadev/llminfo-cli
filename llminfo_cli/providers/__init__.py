"""Provider implementations and configuration loading"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

from llminfo_cli.providers.base import Provider
from llminfo_cli.providers.generic import GenericProvider
from llminfo_cli.providers.parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser

__all__ = ["Provider", "get_provider", "get_providers"]


def _load_builtin_provider_config() -> Dict[str, Any]:
    """Load built-in provider configuration from package data"""
    import importlib.resources
    try:
        # For Python 3.9+
        config_data = importlib.resources.read_text('llminfo_cli.data', 'providers.yml')
        return yaml.safe_load(config_data) or {}
    except:
        # Fallback for other cases
        builtin_path = Path(__file__).parent.parent / "data" / "providers.yml"
        if builtin_path.exists():
            with builtin_path.open() as f:
                return yaml.safe_load(f) or {}
        return {}


def _load_user_provider_config() -> Dict[str, Any]:
    """Load user provider configuration from config directory"""
    config_dir = Path.home() / ".config" / "llminfo"
    config_path = config_dir / "providers.yml"

    if not config_path.exists():
        return {}

    with config_path.open() as f:
        return yaml.safe_load(f) or {}


def _load_provider_config() -> Dict[str, Any]:
    """Load provider configuration from both built-in and user configs"""
    builtin_config = _load_builtin_provider_config()
    user_config = _load_user_provider_config()

    # Merge configurations (user config overrides built-in)
    providers = builtin_config.get("providers", {}).copy()
    providers.update(user_config.get("providers", {}))

    return {"providers": providers}


def _create_provider_from_config(
    name: str, config: Dict[str, Any], api_key: str | None = None
) -> Provider:
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


def get_provider(name: str, api_key: str | None = None) -> Provider:
    """Get provider by name"""
    config = _load_provider_config()
    providers_config = config.get("providers", {})

    if name not in providers_config:
        raise ValueError(f"Unknown provider: {name}")

    return _create_provider_from_config(name, providers_config[name], api_key=api_key)


def get_providers() -> Dict[str, Provider]:
    """Get all configured providers"""
    providers: Dict[str, Provider] = {}

    config = _load_provider_config()
    providers_config = config.get("providers", {})

    for name, provider_config in providers_config.items():
        providers[name] = _create_provider_from_config(name, provider_config)

    return providers
