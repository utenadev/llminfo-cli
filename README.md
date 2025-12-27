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

### List Free Models

```bash
# List free models from all providers
llminfo list free

# List free models from a specific provider
llminfo list free --provider openrouter

# Output in JSON format
llminfo list free --json
```

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
Provider    Model ID                           Context    Price (Prompt/1M)
--------    --------------------------------        -------    -----------------
OpenRouter  openai/gpt-4o-mini:free           128K       $0.00
OpenRouter  google/gemini-1.5-flash:free       1M         $0.00
```

### JSON Format

```json
{
  "provider": "openrouter",
  "models": [
    {
      "id": "openai/gpt-4o-mini:free",
      "name": "GPT-4o Mini",
      "context_length": 128000,
      "pricing": {
        "prompt": "0.00015",
        "completion": "0.0006"
      },
      "is_free": true
    }
  ]
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
git clone https://github.com/yourusername/llminfo-cli.git
cd llminfo-cli

# Install development dependencies
pip install -e ".[dev]"

# Run unit tests
pytest

# Run integration tests (requires API key)
# Install dotenvx first: curl -fsSL https://dotenvx.sh | sh
# Encrypt your .env.test: dotenvx encrypt -f .env.test
# Then run: dotenvx run -f .env.test -- pytest -m integration

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
