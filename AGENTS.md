# AGENTS.md

This file provides guidelines for agentic coding assistants working on the llminfo-cli repository.

## Important Guidelines

### Approval Required for Implementation and Git Operations
**CRITICAL**: Do NOT implement features or make git commits without explicit user approval.

1. **Before Implementing**:
   - Confirm with user before writing any new code
   - Ask for clarification if requirements are ambiguous
   - Explain plan and get approval before proceeding

2. **Before Git Commits**:
   - Confirm with user before running `git add` or `git commit`
   - Show changes with `git status` and `git diff` first
   - Get explicit approval before committing

3. **Restoring Features**:
   - Do NOT restore or reimplement deleted features without user approval
   - If a user mentions "original" or "previously existing" features, ask for clarification before implementing
   - Confirm exact requirements before making any changes

This prevents unauthorized changes and ensures alignment with project goals.

## Build/Lint/Test Commands