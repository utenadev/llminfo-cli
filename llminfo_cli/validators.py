"""Validation functions for provider configurations"""

from typing import Dict, Any


def validate_provider_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """Validate provider configuration

    Returns:
        (is_valid, error_message)
    """
    required_fields = ["name", "base_url", "api_key_env", "models_endpoint", "parser"]

    for field in required_fields:
        if field not in config:
            return False, f"Missing required field: {field}"

    name = config.get("name")
    if not name or not isinstance(name, str):
        return False, "Invalid or missing 'name' field"

    base_url = config.get("base_url")
    if not base_url or not isinstance(base_url, str):
        return False, "Invalid or missing 'base_url' field"

    if not base_url.startswith(("http://", "https://")):
        return False, "Invalid base_url: must start with http:// or https://"

    api_key_env = config.get("api_key_env")
    if not api_key_env or not isinstance(api_key_env, str):
        return False, "Invalid or missing 'api_key_env' field"

    if not api_key_env.isupper():
        return False, "api_key_env should be uppercase"

    models_endpoint = config.get("models_endpoint")
    if not models_endpoint or not isinstance(models_endpoint, str):
        return False, "Invalid or missing 'models_endpoint' field"

    parser = config.get("parser")
    valid_parsers = ["openai_compatible", "openrouter"]
    if parser not in valid_parsers:
        return False, f"Invalid parser: must be one of {valid_parsers}"

    if "credits_endpoint" in config and config["credits_endpoint"] is not None:
        if not isinstance(config["credits_endpoint"], str):
            return False, "Invalid 'credits_endpoint': must be a string or null"

    return True, ""
