"""Tests for response parsers edge cases"""

import pytest
from llminfo_cli.providers.parsers import OpenAICompatibleParser, OpenRouterParser


class TestOpenAICompatibleParser:
    """Test OpenAI compatible parser edge cases"""

    def test_parse_models_with_empty_data(self):
        """Test parsing models with empty data array"""
        parser = OpenAICompatibleParser()
        response = {"data": []}

        models = parser.parse_models(response)

        assert len(models) == 0

    def test_parse_models_with_missing_fields(self):
        """Test parsing models with missing optional fields"""
        parser = OpenAICompatibleParser()
        response = {
            "data": [
                {"id": "model1"},  # Missing name and context_length
                {"id": "model2", "name": "Model 2"},  # Missing context_length
            ]
        }

        models = parser.parse_models(response)

        assert len(models) == 2
        assert models[0].id == "model1"
        assert models[0].name == "model1"  # Should default to id
        assert models[0].context_length is None
        assert models[1].id == "model2"
        assert models[1].name == "model2"  # OpenAI parser defaults name to id
        assert models[1].context_length is None

    def test_parse_models_with_malformed_data(self):
        """Test parsing models with malformed data"""
        parser = OpenAICompatibleParser()

        # Test with None data
        response = {"data": None}
        models = parser.parse_models(response)
        assert len(models) == 0

        # Test with non-list data
        response = {"data": "not_a_list"}
        models = parser.parse_models(response)
        assert len(models) == 0

        # Test with missing data key
        response = {}
        models = parser.parse_models(response)
        assert len(models) == 0

    def test_parse_credits_not_implemented(self):
        """Test that parse_credits returns None (not implemented)"""
        parser = OpenAICompatibleParser()
        result = parser.parse_credits({"some": "data"})
        assert result is None


class TestOpenRouterParser:
    """Test OpenRouter parser edge cases"""

    def test_parse_models_with_empty_data(self):
        """Test parsing models with empty data array"""
        parser = OpenRouterParser()
        response = {"data": []}

        models = parser.parse_models(response)

        assert len(models) == 0

    def test_parse_models_with_missing_optional_fields(self):
        """Test parsing models with missing optional fields"""
        parser = OpenRouterParser()
        response = {
            "data": [
                {"id": "model1", "name": "Model 1"},  # Missing context_length and pricing
                {"id": "model2", "name": "Model 2", "context_length": 8192},  # Missing pricing
            ]
        }

        models = parser.parse_models(response)

        assert len(models) == 2
        assert models[0].id == "model1"
        assert models[0].name == "Model 1"
        assert models[0].context_length is None
        assert models[0].pricing is None
        assert models[1].id == "model2"
        assert models[1].name == "Model 2"
        assert models[1].context_length == 8192
        assert models[1].pricing is None

    def test_parse_models_with_malformed_data(self):
        """Test parsing models with malformed data"""
        parser = OpenRouterParser()

        # Test with missing data key
        response = {}
        models = parser.parse_models(response)
        assert len(models) == 0

        # Test with empty list data
        response = {"data": []}
        models = parser.parse_models(response)
        assert len(models) == 0

        # Test with non-list data (should raise TypeError)
        response = {"data": "not_a_list"}
        with pytest.raises(TypeError):
            parser.parse_models(response)

    def test_parse_models_with_incomplete_model_data(self):
        """Test parsing models with incomplete model data"""
        parser = OpenRouterParser()
        response = {
            "data": [
                {"id": "model1"},  # Missing name (should raise error)
            ]
        }

        # OpenRouter parser expects both id and name
        with pytest.raises(KeyError):
            parser.parse_models(response)

    def test_parse_credits_with_valid_data(self):
        """Test parsing credits with valid data"""
        parser = OpenRouterParser()
        response = {"data": {"total_credits": 100.50, "total_usage": 25.25}}

        credits = parser.parse_credits(response)

        assert credits is not None
        assert credits.total_credits == 100.50
        assert credits.usage == 25.25
        assert credits.remaining == 75.25

    def test_parse_credits_with_missing_data(self):
        """Test parsing credits with missing data"""
        parser = OpenRouterParser()

        # Test with missing data key
        response = {}
        credits = parser.parse_credits(response)
        # Should return CreditInfo with default values
        assert credits is not None
        assert credits.total_credits == 0.0
        assert credits.usage == 0.0
        assert credits.remaining == 0.0

    def test_parse_credits_with_zero_values(self):
        """Test parsing credits with zero values"""
        parser = OpenRouterParser()
        response = {"data": {"total_credits": 0.0, "total_usage": 0.0}}

        credits = parser.parse_credits(response)

        assert credits is not None
        assert credits.total_credits == 0.0
        assert credits.usage == 0.0
        assert credits.remaining == 0.0


class TestParserConfiguration:
    """Test parser configuration and initialization"""

    def test_openai_compatible_parser_with_custom_path(self):
        """Test OpenAI compatible parser with custom model path"""
        parser = OpenAICompatibleParser(model_path="models")

        response = {"models": [{"id": "model1", "name": "Model 1"}]}

        models = parser.parse_models(response)
        assert len(models) == 1
        assert models[0].id == "model1"

    def test_openai_compatible_parser_with_credit_path(self):
        """Test OpenAI compatible parser with credit path"""
        parser = OpenAICompatibleParser(credit_path="billing")

        # Should still return None since parse_credits is not implemented
        result = parser.parse_credits({"billing": "data"})
        assert result is None
