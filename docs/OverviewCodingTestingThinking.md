# Overview: Coding & Testing for Human-LLM Collaboration

This document outlines coding and testing standards optimized for a workflow where Humans and LLMs build software together.
The goal is to write code that is not only executable by Python but also **understandable and verifiable by the AI Agent**.

## 1. Coding Standards: "Type Hints as Guardrails"

For LLMs, Python's dynamic nature can be a double-edged sword. Strong typing is the most effective way to constrain the LLM's output and prevent logical hallucinations.

### 1.1 Strict Type Hinting
- **Why**: Type hints act as "inline documentation" that the LLM respects.
- **Rule**:
    - **No `Any`**: Avoid `Any`. It tells the LLM "do whatever you want," which leads to bugs.
    - **Pydantic Models**: Use Pydantic for data structures. It forces the LLM to structure data exactly as defined.
    - **Return Types**: Always define return types. This helps the LLM understand data flow across functions.

    ```python
    # BAD (LLM might return a dict, None, or raise error unpredictably)
    def get_data(id): ...

    # GOOD (LLM knows exactly what to return)
    def get_data(user_id: str) -> UserProfile | None: ...
    ```

### 1.2 "Self-Documenting" Code
- **Docstrings**: Write docstrings *before* the function body. This serves as a prompt for the LLM to complete the implementation.
- **Variable Names**: Use descriptive names (`user_id_str` vs `uid`). LLMs rely heavily on semantic naming to infer intent.

## 2. Testing Strategy: "The Agent's Reality Check"

LLMs cannot "run" code in their head perfectly. Tests serve as the external reality check.

### 2.1 Test-Driven Generation (TDG)
Instead of "Code then Test", prefer:
1. **Human**: Write the test case (or ask LLM to write it based on Spec).
2. **LLM**: Write implementation to pass the test.
3. **Agent**: Run test. If fail, analyze error, fix code.

### 2.2 Mocking External Dependencies
- **Constraint**: LLMs often hallucinate API responses.
- **Solution**: Explicitly provide example API responses (JSON) in the prompt or test files.
- **Rule**: All external I/O (HTTP, DB) must be mocked. This allows the LLM to iterate rapidly without hitting rate limits or needing real credentials.

## 3. Automation Interface: "Taskfile"

The AI Agent (and the Human) needs a deterministic way to perform development tasks without memorizing complex flags. We use `go-task` (Taskfile.yml).

### 3.1 Standard Tasks
The Agent should be able to rely on these commands existing:

- `task setup`: Prepare the environment.
- `task test`: Run verification.
- `task lint`: Check code style.
- **`task check`**: The "Gold Standard". Runs format -> lint -> type-check -> test.
    - **Agent Rule**: Always run `task check` before declaring a task complete.

### 3.2 Error Feedback Loop
When `task check` fails, the output is the feedback mechanism for the LLM.
- **Lint Errors**: LLM fixes syntax/style.
- **Type Errors (mypy)**: LLM fixes logical inconsistencies.
- **Test Failures**: LLM fixes implementation bugs.

## 4. Project Structure (Scale-Dependent)

Organize files so the LLM can easily find context.

### Level 1: Simple Script
```
project/
├── main.py        # Logic + CLI
├── test_main.py   # One file to verify everything
└── Taskfile.yml   # Simple run/test commands
```

### Level 2: Standard Application (This Template)
```
project/
├── app_name/
│   ├── main.py    # Entry point
│   ├── core/      # Business Logic (Pure Python, high test coverage)
│   └── cli.py     # Typer/Click definitions
├── tests/         # Mirrors source structure
├── providers.yml  # Configuration (Logic separated from Settings)
├── Taskfile.yml   # Full automation
└── pyproject.toml # Dependencies
```

### Level 3: Large System
Separate "Interface" from "Implementation" to help the LLM focus.
```
project/
├── src/
│   ├── domain/    # Abstract Base Classes (The "Contract")
│   ├── infra/     # Concrete Implementations (The "Details")
│   └── app/       # Application Service
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── SPEC.md
│   └── ARCHITECTURE.md
└── Taskfile.yml
```