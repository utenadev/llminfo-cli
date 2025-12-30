# llminfo-cli

A CLI tool for retrieving and searching available LLM model information from OpenRouter.ai and related AI providers (Groq, Cerebras, Mistral).

## Repository

https://github.com/utenadev/llminfo-cli

## Installation

```bash
pip install llminfo-cli
```

## Environment Setup

Set the following environment variables:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export GROQ_API_KEY="your-groq-api-key"          # optional
export CEREBRAS_API_KEY="your-cerebras-api-key"  # optional
export MISTRAL_API_KEY="your-mistral-api-key"    # optional
```

## Usage

### Getting Started

When you run `llminfo` without arguments, you'll see available commands:

```bash
llminfo

# Output:
# Usage: llminfo [COMMAND] [OPTIONS]
#
# Available commands:
#   credits         Display credit balance for the specified provider
#   list            List models from providers
#   test-provider   Test a provider configuration
#   import-provider Test and import a provider configuration
#
# Run 'llminfo [COMMAND] --help' for command-specific help.
#
# Examples:
#   llminfo list models                    # List all models
#   llminfo credits --provider openrouter  # Check credits
```

### List Models

List models from all or specified providers.

```bash
# List models from all providers
llminfo list models

# List models from a specific provider
llminfo list models --provider openrouter

# Output in JSON format
llminfo list models --json

# Force refresh from API (ignore cache)
llminfo list models --force
```

## Caching

Model lists are cached for 1 hour by default. Cache is stored in `~/.cache/llminfo/`.

To force refresh from API and ignore cache:
```bash
llminfo list models --force
```

### Check Credits

Display credit balance for the specified provider.

```bash
# Check credits for OpenRouter
llminfo credits --provider openrouter

# Check credits for Groq (not supported, will return error)
llminfo credits --provider groq

# Output in JSON format
llminfo credits --provider openrouter --json
```

### Test and Import Providers

Test a new provider configuration and import it into `providers.yml`.

```bash
# Test a provider configuration
llminfo test-provider plugin/new-provider.yml --api-key your-api-key

# Test and import (add to providers.yml)
llminfo import-provider plugin/new-provider.yml --api-key your-api-key
```

### Provider Configuration

Providers are configured in `providers.yml`. OpenAI-compatible providers can be added with just a YAML configuration:

```yaml
providers:
  groq:
    name: "groq"
    base_url: "https://api.groq.com/openai/v1"
    api_key_env: "GROQ_API_KEY"
    models_endpoint: "/models"
    parser: "openai_compatible"
    credits_endpoint: null
```

See `SPEC.md` for detailed provider addition criteria.

## Output Formats

### Table Format (Default)

```
Total Credits: $15.00
Usage: $2.67
Remaining: $12.33
```

### JSON Format

```json
{
  "total_credits": 15.0,
  "usage": 2.66625653,
  "remaining": 12.33374347
}
```

## Available Commands

### Credits

Display credit balance for the specified provider. Note that only OpenRouter supports credits API at this time.

```bash
llminfo credits --provider openrouter
```

### Test Provider

Test a provider configuration without adding it to the permanent configuration.

```bash
llminfo test-provider plugin/new-provider.yml --api-key your-api-key
```

### Import Provider

Test and import a provider configuration into `providers.yml`.

```bash
llminfo import-provider plugin/new-provider.yml --api-key your-api-key
```

## Supported Providers

| Provider | API Key Environment Variable | Model List | Credits |
|----------|-----------------------------|------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` | ✓ | ✓ |
| Groq | `GROQ_API_KEY` | ✓ | ✗ |
| Cerebras | `CEREBRAS_API_KEY` | ✓ | ✗ |
| Mistral | `MISTRAL_API_KEY` | ✓ | ✗ |

## Development

```bash
# Clone repository
git clone https://github.com/utenadev/llminfo-cli.git
cd llminfo-cli

# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run integration tests (requires API key)
# Install dotenvx first: curl -fsSL https://dotenvx.sh | sh
# Encrypt your .env.test: dotenvx encrypt -f .env.test
# Then run: dotenvx run -f .env.test -- pytest -m integration

# Test a new provider plugin
llminfo test-provider plugin/new-provider.yml --api-key your-key

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy llminfo_cli tests
```

## Testing

- **Unit tests**: Mocked API responses, no API key required
- **Integration tests**: Real API calls, require valid API keys (OPENROUTER_API_KEY, GROQ_API_KEY, etc.)

See `tests/INTEGRATION.md` for integration test setup instructions.

## Features

- **Configuration-based providers**: Add OpenAI-compatible providers with just a YAML configuration
- **Plugin system**: Test and import new providers safely
- **Type-safe**: Built with Python type hints and Pydantic models
- **Async API calls**: Non-blocking requests for better performance
- **Multiple providers**: OpenRouter, Groq, Cerebras, Mistral supported
- **Caching**: 1-hour cache for model lists to reduce API calls
- **Cache invalidation**: Use `--force` flag to bypass cache and fetch fresh data

## License

MIT License
