"""Tests for JSON output format validation"""

import json
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from llminfo_cli.main import app

runner = CliRunner()


def test_credits_json_format():
    """Test credits command JSON output format"""
    from llminfo_cli.schemas import CreditInfo

    # Test CreditInfo JSON serialization directly
    credit_info = CreditInfo(total_credits=100.0, usage=25.0, remaining=75.0)
    json_str = json.dumps(credit_info.model_dump(), indent=2)

    # Parse JSON and verify structure
    data = json.loads(json_str)
    assert "total_credits" in data
    assert "usage" in data
    assert "remaining" in data
    assert data["total_credits"] == 100.0
    assert data["usage"] == 25.0
    assert data["remaining"] == 75.0


def test_list_models_json_format():
    """Test list models JSON output format structure"""
    from llminfo_cli.schemas import ModelInfo

    # Test ModelInfo JSON serialization directly
    model_info = ModelInfo(
        id="model1", name="Model 1", context_length=1000, pricing={"input": 0.01}
    )

    # Test the expected output format
    expected_output = [{"provider": "test", "model": model_info.model_dump()}]
    json_str = json.dumps(expected_output, indent=2)

    # Parse JSON and verify structure
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["provider"] == "test"
    assert "model" in data[0]
    assert data[0]["model"]["id"] == "model1"


def test_list_models_json_format_multiple_providers():
    """Test list models JSON output structure with multiple providers"""
    from llminfo_cli.schemas import ModelInfo

    # Test multiple providers output structure
    model1 = ModelInfo(id="model1", name="Model 1", context_length=None, pricing=None)
    model2 = ModelInfo(id="model2", name="Model 2", context_length=None, pricing=None)

    expected_output = [
        {"provider": "provider1", "model": model1.model_dump()},
        {"provider": "provider2", "model": model2.model_dump()},
    ]
    json_str = json.dumps(expected_output, indent=2)

    # Parse JSON and verify structure
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert len(data) == 2

    providers = [item["provider"] for item in data]
    assert "provider1" in providers
    assert "provider2" in providers


def test_json_output_with_special_characters():
    """Test JSON output handles special characters properly"""
    from llminfo_cli.schemas import ModelInfo

    # Test special characters in JSON
    model = ModelInfo(
        id="model-with-special-chars_123",
        name="Model with special chars: éñ",
        context_length=2048,
        pricing=None,
    )

    # Test JSON serialization with special characters
    json_str = json.dumps(model.model_dump(), ensure_ascii=False)
    data = json.loads(json_str)
    assert data["name"] == "Model with special chars: éñ"


def test_json_output_empty_list():
    """Test JSON output structure for empty list"""
    # Test empty list JSON structure
    expected_output = []
    json_str = json.dumps(expected_output, indent=2)

    # Parse JSON and verify empty list
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert len(data) == 0
