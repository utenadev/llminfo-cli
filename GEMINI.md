# llminfo-cli Context Guide

## Project Overview

`llminfo-cli` is a Python-based command-line interface tool designed to retrieve and search for Large Language Model (LLM) information from various AI providers.

**Key Features:**
*   **Model Listing:** Fetch available models from OpenRouter, Groq, Cerebras, Mistral, and other OpenAI-compatible providers.
*   **Credit Checking:** Check account credit balances (currently supported for OpenRouter).
*   **Provider Management:** Configuration-based provider system (`providers.yml`) allowing easy addition of OpenAI-compatible APIs.
*   **Plugin System:** Test (`test-provider`) and import (`import-provider`) new provider configurations safely.
*   **Caching:** Caches model lists to reduce API calls (default TTL: 1 hour).
*   **Async Operations:** Built with `asyncio` and `httpx` for non-blocking API requests.

## Architecture & Technology Stack

*   **Language:** Python 3.11+
*   **CLI Framework:** `typer` (with `rich` for formatting)
*   **HTTP Client:** `httpx` (async)
*   **Data Validation:** `pydantic`
*   **Configuration:** `pyyaml`
*   **Build System:** `hatchling` (configured in `pyproject.toml`)

### Directory Structure
*   `llminfo_cli/`: Source code.
    *   `main.py`: Entry point and CLI command definitions.
    *   `providers/`: Provider logic (GenericProvider, OpenRouterProvider).
        *   `parsers.py`: Response parsing logic (Strategy Pattern).
    *   `schemas.py`: Pydantic models for data structures.
*   `providers.yml`: Central configuration for supported providers.
*   `tests/`: Unit and integration tests.
*   `plugin/`: Directory for testing new provider plugins (gitignored).

## Development Workflow

### Installation
To set up the development environment:
```bash
pip install -e ".[dev]"
```

### Running the CLI
The entry point is defined in `pyproject.toml` as `llminfo`.
```bash
llminfo list models
llminfo credits --provider openrouter
```

### Testing
*   **Unit Tests:** Run all tests (mocked, no API key needed).
    ```bash
    pytest
    ```
*   **Integration Tests:** Require real API keys and `dotenvx`.
    ```bash
    dotenvx run -f .env.test -- pytest -m integration
    ```
*   **Code Quality:**
    *   Linting: `ruff check .`
    *   Formatting: `ruff format .`
    *   Type Checking: `mypy llminfo_cli tests`

## Agent Guidelines (from AGENTS.md)
*   **Approval Required:** Do NOT implement features or commit changes without explicit user approval.
*   **Git Operations:** Always run `git status` and `git diff` before asking to commit.
*   **Feature Preservation:** Do not remove existing features without explicit instruction.

## Roadmap & Future Work (from BLUEPRINT.md)
*   **v1.1:** Multi-provider price comparison, model details (`llminfo info`), filtering (`--filter`).
*   **v1.2:** Interactive mode (TUI), model evaluation, custom parser plugins.

## Key Files
*   `pyproject.toml`: Project dependencies, build config, and script definitions.
*   `providers.yml`: Central configuration for defining API providers.
*   `llminfo_cli/main.py`: Main application logic and CLI entry point.
*   `docs/SPEC.md`: Functional requirements and specification details.
*   `AGENTS.md`: Rules for AI agents working on this repo.
*   `docs/BLUEPRINT.md`: Detailed design and roadmap (Japanese).