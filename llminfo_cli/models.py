"""Model selection logic"""

from typing import List

from llminfo_cli.schemas import ModelInfo


def select_best_free_model(models: List[ModelInfo]) -> ModelInfo:
    """
    Select the best free model for AgentCodingTool usage

    Priority:
    1. context_length > 32,000 (for long code generation)
    2. Low price
    3. Model name preference (gpt, gemini, claude)
    """
    free_models = [m for m in models if m.is_free]

    if not free_models:
        raise ValueError("No free models available")

    # Filter by context length
    candidates = [m for m in free_models if (m.context_length or 0) > 32000]

    # If no models meet context requirement, use all free models
    if not candidates:
        candidates = free_models

    # Sort by price (lower is better)
    candidates.sort(key=lambda m: float(m.pricing.get("prompt", "999999")) if m.pricing else 999999)

    return candidates[0]
