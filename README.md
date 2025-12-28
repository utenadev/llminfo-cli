# llminfo-cli

A CLI tool for retrieving and searching available LLM model information from OpenRouter.ai and related AI providers (Groq, Cerebras, Mistral).

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

### Check Credits

Display credit balance for the specified provider.

```bash
# Check credits for OpenRouter
llminfo credits --provider openrouter

# Check credits for Groq (not supported)
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

### Select Best Free Model

Selects the best free model suitable for AgentCodingTool usage.

```bash
llminfo best-free

# Select from a specific provider
llminfo best-free --provider openrouter

# Output in JSON format
llminfo best-free --json
```

### Check Credits

Display credit balance for OpenRouter.

```bash
llminfo credits openrouter

# Output in JSON format
llminfo credits openrouter --json
```

### List All Models

```bash
# List all models from all providers
llminfo list models

# List models from a specific provider
llminfo list models --provider groq
```

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
mypy llminfo_cli
```

## Testing

- **Unit tests**: Mocked API responses, no API key required
- **Integration tests**: Real API calls, require valid OpenRouter API key

See `tests/INTEGRATION.md` for integration test setup instructions.

## License

MIT License
