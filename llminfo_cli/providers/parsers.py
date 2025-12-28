"""Response parser strategies for provider implementations"""

from abc import ABC, abstractmethod
from typing import List, Optional

from llminfo_cli.schemas import CreditInfo, ModelInfo


class ResponseParser(ABC):
    """Base class for response parsing strategies"""

    @abstractmethod
    def parse_models(self, response: dict) -> List[ModelInfo]:
        """Parse models from API response"""

    @abstractmethod
    def parse_credits(self, response: dict) -> Optional[CreditInfo]:
        """Parse credits from API response"""


class OpenAICompatibleParser(ResponseParser):
    """Parser for OpenAI-compatible API responses"""

    def __init__(self, model_path: str = "data", credit_path: Optional[str] = None):
        self.model_path = model_path
        self.credit_path = credit_path

    def parse_models(self, response: dict) -> List[ModelInfo]:
        data = response.get(self.model_path, [])

        if isinstance(data, list):
            return [
                ModelInfo(
                    id=m.get("id", ""),
                    name=m.get("id", ""),
                    context_length=m.get("context_length"),
                    pricing=m.get("pricing"),
                )
                for m in data
            ]
        return []

    def parse_credits(self, response: dict) -> Optional[CreditInfo]:
        if not self.credit_path:
            return None
        return None


class OpenRouterParser(ResponseParser):
    """Custom parser for OpenRouter API responses"""

    def parse_models(self, response: dict) -> List[ModelInfo]:
        data = response.get("data", [])

        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                context_length=m.get("context_length"),
                pricing=m.get("pricing"),
            )
            for m in data
        ]

    def parse_credits(self, response: dict) -> Optional[CreditInfo]:
        data = response.get("data", {})

        total_credits = data.get("total_credits", 0.0)
        total_usage = data.get("total_usage", 0.0)

        return CreditInfo(
            total_credits=total_credits,
            usage=total_usage,
            remaining=total_credits - total_usage,
        )
