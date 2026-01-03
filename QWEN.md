# llminfo-cli - QWEN Context Guide

## Project Overview

`llminfo-cli` is a Python-based command-line interface tool designed to retrieve and search for Large Language Model (LLM) information from various AI providers. The tool provides a unified interface to access model information from OpenRouter, Groq, Cerebras, Mistral, and other OpenAI-compatible providers.

**Key Features:**
* **Model Listing:** Fetch available models from multiple providers with detailed information
* **Credit Checking:** Check account credit balances (currently supported for OpenRouter)
* **Provider Management:** Configuration-based provider system (`providers.yml`) allowing easy addition of OpenAI-compatible APIs
* **Plugin System:** Test (`test-provider`) and import (`import-provider`) new provider configurations safely
* **Caching:** Caches model lists to reduce API calls (default TTL: 1 hour)
* **Async Operations:** Built with `asyncio` and `httpx` for non-blocking API requests
* **Multiple Output Formats:** Support for both table (default) and JSON output formats

## Architecture & Technology Stack

* **Language:** Python 3.11+
* **CLI Framework:** `typer` (with `rich` for formatting)
* **HTTP Client:** `httpx` (async)
* **Data Validation:** `pydantic`
* **Configuration:** `pyyaml`
* **Build System:** `hatchling` (configured in `pyproject.toml`)

### Directory Structure
```
llminfo-cli/
├── llminfo_cli/                 # Source code
│   ├── __init__.py
│   ├── main.py                  # Entry point and CLI command definitions
│   ├── cache.py                 # Cache management
│   ├── errors.py                # Error definitions
│   ├── schemas.py               # Pydantic data models
│   ├── validators.py            # Provider configuration validators
│   └── providers/               # Provider logic
│       ├── __init__.py          # Provider factory
│       ├── base.py              # Provider base class
│       ├── generic.py           # Generic provider implementation
│       ├── openrouter.py        # OpenRouter-specific provider
│       └── parsers.py           # Response parsing logic (Strategy Pattern)
├── tests/                       # Unit and integration tests
├── plugin/                      # Directory for testing new provider plugins (gitignored)
├── providers.yml                # Central configuration for supported providers
├── pyproject.toml               # Project dependencies and build config
├── README.md                    # Main documentation
├── docs/
│   ├── SPEC.md                  # Functional requirements and specification
│   └── BLUEPRINT.md             # Detailed design and roadmap
```

## Core Components

### Data Models (schemas.py)
* `ModelInfo`: Represents model information with fields for id, name, context_length, and pricing
* `CreditInfo`: Represents credit information with total_credits, usage, and remaining fields

### Provider System
* **GenericProvider**: Base implementation for OpenAI-compatible providers
* **ResponseParser Strategy**: Abstract base class with concrete implementations:
  * `OpenAICompatibleParser`: For standard OpenAI-compatible APIs
  * `OpenRouterParser`: For OpenRouter-specific response format
* **Provider Factory**: Dynamically creates provider instances from configuration

### Cache Management (cache.py)
* Caches model lists in `~/.cache/llminfo/` directory
* Default TTL of 1 hour, configurable per provider
* Supports cache invalidation with `--force` flag

## CLI Commands

### Main Commands
* `llminfo list models`: List models from all or specific providers
* `llminfo credits`: Display credit balance for specified provider
* `llminfo test-provider`: Test a provider configuration file
* `llminfo import-provider`: Test and import a provider configuration

### Global Options
* `--json`: Output in JSON format instead of table
* `--provider`: Specify a specific provider
* `--force`: Force refresh from API (ignore cache)

## Building and Running

### Installation
```bash
# Install for development
pip install -e ".[dev]"

# Install as package
pip install llminfo-cli
```

### Running the CLI
The entry point is defined in `pyproject.toml` as `llminfo`:
```bash
llminfo list models
llminfo credits --provider openrouter
llminfo list models --json
llminfo list models --force
```

### Development Commands
```bash
# Run all tests
pytest

# Run integration tests (requires API keys)
dotenvx run -f .env.test -- pytest -m integration

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy llminfo_cli tests
```

## Provider Configuration

Providers are configured in `providers.yml` using a YAML format:
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

### Adding New Providers
Providers that follow OpenAI-compatible API patterns can be added with just a YAML configuration. Custom providers require implementing a new provider class.

### Provider Addition Criteria
**Configuration-based (OpenAI-compatible)** providers must meet:
1. Base URL + `/models` endpoint for model listing
2. API key authentication: `Authorization: Bearer <token>`
3. Response structure: `{"data": [...]}` or simple array
4. Standard HTTP status codes (200, 401, 429)

**Custom implementation** required if:
1. Custom authentication (different header names, signatures required)
2. Nested model information structure
3. Complex credit information transformations
4. Pagination or special parameters needed

## Testing Strategy

### Test Types
* **Unit Tests**: Mocked API responses, no API key required
* **Integration Tests**: Real API calls, require valid API keys
* **CLI Command Tests**: Test command-line interface functionality

### Test Organization
* Located in `tests/` directory
* Use pytest framework with pytest-asyncio for async tests
* Include error handling tests for HTTP status codes and network errors

## Development Conventions

### Code Quality
* Python 3.11+ with type hints
* Pydantic for data validation
* Ruff for linting and formatting
* MyPy for static type checking

### Error Handling
* Comprehensive error handling for HTTP status codes (401, 429, etc.)
* Network error handling with appropriate user feedback
* Validation of provider configurations

### Logging
* Comprehensive logging to both console and `llminfo.log` file
* Structured logging with appropriate log levels
* No API keys logged for security

## Environment Variables

Required API keys:
* `OPENROUTER_API_KEY` - OpenRouter API key
* `GROQ_API_KEY` - Groq API key
* `CEREBRAS_API_KEY` - Cerebras API key
* `MISTRAL_API_KEY` - Mistral API key

## Security Considerations

* API keys stored only in environment variables
* Plugin files (in `plugin/`) are git-ignored
* No API keys included in logs
* HTTPS communication only

## Roadmap & Future Work

### v1.1 Features (Planned)
* Multi-provider price comparison
* Model details (`llminfo info`)
* Filtering (`--filter` option)

### v1.2 Features (Planned)
* Interactive mode (TUI)
* Model evaluation
* Custom parser plugins

## Key Files
* `pyproject.toml`: Project dependencies, build config, and script definitions
* `providers.yml`: Central configuration for defining API providers
* `llminfo_cli/main.py`: Main application logic and CLI entry point
* `docs/SPEC.md`: Functional requirements and specification details
* `AGENTS.md`: Rules for AI agents working on this repo
* `docs/BLUEPRINT.md`: Detailed design and roadmap (Japanese)

## Agent Guidelines
* **Approval Required:** Do NOT implement features or commit changes without explicit user approval
* **Git Operations:** Always run `git status` and `git diff` before asking to commit
* **Feature Preservation:** Do not remove existing features without explicit instruction
* **Language Convention:** Conversations with user are in Japanese, but source code comments and commit messages should be in English
* **Testing:** Maintain comprehensive test coverage when making changes