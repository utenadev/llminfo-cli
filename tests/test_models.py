"""Tests for model selection logic"""

import pytest

from llminfo_cli.models import select_best_free_model
from llminfo_cli.schemas import ModelInfo


def test_select_best_free_model():
    """Test selecting best free model"""
    models = [
        ModelInfo(
            id="model1",
            name="Model 1",
            context_length=32000,
            is_free=True,
            pricing={"prompt": "0.01"},
        ),
        ModelInfo(
            id="model2",
            name="Model 2",
            context_length=131072,
            is_free=True,
            pricing={"prompt": "0.00"},
        ),
    ]

    selected = select_best_free_model(models)
    assert selected.id == "model2"
    assert selected.context_length == 131072


def test_select_best_free_model_no_context():
    """Test selecting best free model when context length is None"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=None, is_free=True),
        ModelInfo(id="model2", name="Model 2", context_length=1000, is_free=True, pricing={}),
    ]

    selected = select_best_free_model(models)
    assert selected.id == "model1"


def test_select_best_free_model_no_free_models():
    """Test error when no free models are available"""
    models = [
        ModelInfo(id="model1", name="Model 1", is_free=False),
        ModelInfo(id="model2", name="Model 2", is_free=False),
    ]

    with pytest.raises(ValueError, match="No free models available"):
        select_best_free_model(models)
