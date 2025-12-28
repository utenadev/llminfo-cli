"""Abstract base class for provider implementations"""

from abc import ABC, abstractmethod
from typing import List, Optional

from llminfo_cli.schemas import CreditInfo, ModelInfo


class Provider(ABC):
    """Abstract base class for all AI providers"""

    @abstractmethod
    async def get_models(self, use_cache: bool = True) -> List[ModelInfo]:
        """Fetch list of available models"""
        pass

    @abstractmethod
    async def get_credits(self) -> Optional[CreditInfo]:
        """Fetch credit information (if available)"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name identifier"""
        pass
