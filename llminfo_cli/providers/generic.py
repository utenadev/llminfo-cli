"""Generic provider implementation for configuration-based providers"""

import os
from typing import List, Optional

import httpx

from .base import Provider
from .parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser
from ..schemas import CreditInfo, ModelInfo


class GenericProvider(Provider):
    """Generic provider implementation for configuration-based providers"""

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key_env: str,
        models_endpoint: str,
        parser: ResponseParser,
        api_key: Optional[str] = None,
        credits_endpoint: Optional[str] = None,
    ):
        self.provider_name_value = provider_name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env)
        self.models_endpoint = models_endpoint
        self.parser = parser
        self.credits_endpoint = credits_endpoint

    async def get_models(self) -> List[ModelInfo]:
        """Fetch list of available models from provider"""
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.models_endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return self.parser.parse_models(data)

    async def get_credits(self) -> Optional[CreditInfo]:
        """Fetch credit information from provider"""
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        if not self.credits_endpoint:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.credits_endpoint}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return self.parser.parse_credits(data)

    @property
    def provider_name(self) -> str:
        """Provider name"""
        return self.provider_name_value


class ProviderFactory:
    """Factory for creating provider instances from configuration"""

    @staticmethod
    def create_openai_compatible(
        provider_name: str,
        base_url: str,
        api_key_env: str,
        models_endpoint: str = "/models",
        credits_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> GenericProvider:
        """Create an OpenAI-compatible provider"""
        parser = OpenAICompatibleParser(model_path="data")
        return GenericProvider(
            provider_name=provider_name,
            base_url=base_url,
            api_key_env=api_key_env,
            models_endpoint=models_endpoint,
            parser=parser,
            api_key=api_key,
            credits_endpoint=credits_endpoint,
        )

    @staticmethod
    def create_openrouter(api_key: Optional[str] = None) -> GenericProvider:
        """Create an OpenRouter provider"""
        parser = OpenRouterParser()
        return GenericProvider(
            provider_name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            models_endpoint="/models",
            parser=parser,
            api_key=api_key,
            credits_endpoint="/credits",
        )
