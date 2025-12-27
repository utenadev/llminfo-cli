# AGENTS.md

This file provides guidelines for agentic coding assistants working on the llminfo-cli repository.

## Build/Lint/Test Commands

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=llminfo_cli --cov-report=html

# Run a specific test file
pytest tests/test_providers.py

# Run a specific test function
pytest tests/test_providers.py::test_openrouter_get_models

# Run async tests
pytest -v
```

### Linting and Formatting
```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy llminfo_cli
```

### Development Setup
```bash
# Install dependencies
pip install -e ".[dev]"

# Run the CLI
llminfo list free
llminfo best-free
llminfo credits
```

## Code Style Guidelines

### Project Structure
```
llminfo_cli/
├── main.py              # CLI entry point using typer
├── models.py             # Model selection logic
├── schemas.py            # Pydantic data models
└── providers/
    ├── base.py          # Abstract base class
    ├── openrouter.py    # OpenRouter implementation
    ├── groq.py          # Groq implementation
    ├── cerebras.py      # Cerebras implementation
    └── mistral.py       # Mistral implementation
```

### Python Conventions
- **Python Version**: 3.11+
- **Line Length**: 100 characters (configured in pyproject.toml)
- **Indentation**: 4 spaces
- All functions must have type hints for parameters and return values
- Use `Optional[T]` for nullable types, `List[T]`, `Dict[K, V]` from `typing`
- Use `ABC` and `@abstractmethod` for abstract base classes

### Imports
- Use isort-style grouping (stdlib, third-party, local)
- Keep imports at top of files, use absolute imports for local modules

### Data Models
- Use Pydantic `BaseModel` for all data structures in `schemas.py`
- Use field descriptions for clarity

### Async/Await Patterns
- Use `async def` for async functions with proper `await`
- Use `httpx.AsyncClient()` with context managers for HTTP requests

### CLI Structure (Typer)
- Use `typer.Typer()` for main app
- Use `@app.command()` for CLI commands, `@app.callback()` for global options
- Use `typer.Option()` for command options

### Error Handling
- Handle `httpx.HTTPStatusError` and `httpx.RequestError` specifically
- Use descriptive error messages with appropriate exit codes
- Check environment variables before API calls

### Environment Variables
- Store API keys as environment variables using `os.environ.get()`
- Define env var names as class constants (e.g., `API_KEY_ENV`)

### Testing
- Use `@pytest.mark.asyncio` for async tests
- Mock HTTP responses using `pytest-mock` or `unittest.mock`
- Test both success and error cases

### Constants
- Define constants as class attributes or module-level constants
- Use UPPER_CASE for module-level constants
- API URLs should be class constants

### Output Formatting
- Use `rich` library for table formatting (default output)
- Support JSON output with `--json` flag
- Use `typer.echo()` for console output

### Provider Implementation Pattern
All providers must:
1. Inherit from `Provider` base class
2. Implement `get_models()` method (async)
3. Implement `get_credits()` method (async, can return None)
4. Implement `provider_name` property
5. Define `BASE_URL` and `API_KEY_ENV` constants
