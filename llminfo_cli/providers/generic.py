"""Generic provider implementation for configuration-based providers"""

import os
from typing import List, Optional

import httpx

from .base import Provider
from .parsers import OpenAICompatibleParser, OpenRouterParser, ResponseParser
from ..cache import CacheManager
from ..schemas import CreditInfo, ModelInfo
from ..errors import APIError, AuthenticationError, RateLimitError, NetworkError


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
        cache_ttl_hours: int = 1,
    ):
        self.provider_name_value = provider_name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env)
        self.models_endpoint = models_endpoint
        self.parser = parser
        self.credits_endpoint = credits_endpoint
        self.cache_manager = CacheManager(ttl_hours=cache_ttl_hours)

    async def get_models(self, use_cache: bool = True) -> List[ModelInfo]:
        """Fetch list of available models from provider"""
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        if use_cache:
            cached_models = await self.cache_manager.get(self.provider_name_value)
            if cached_models is not None:
                return cached_models

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.models_endpoint}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                models = self.parser.parse_models(data)

            await self.cache_manager.set(self.provider_name_value, models)

            return models
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed for provider {self.provider_name_value}",
                    provider=self.provider_name_value
                ) from e
            elif status_code == 429:
                raise RateLimitError(
                    f"Rate limit exceeded for provider {self.provider_name_value}",
                    provider=self.provider_name_value
                ) from e
            else:
                raise APIError(
                    f"API request failed with status {status_code} for provider {self.provider_name_value}",
                    status_code=status_code,
                    provider=self.provider_name_value
                ) from e
        except httpx.RequestError as e:
            raise NetworkError(
                f"Network error occurred for provider {self.provider_name_value}",
                original_error=e
            ) from e

    async def get_credits(self) -> Optional[CreditInfo]:
        """Fetch credit information from provider"""
        if not self.api_key:
            raise ValueError(f"{self.api_key_env} environment variable not set")

        if not self.credits_endpoint:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.credits_endpoint}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                credits_info = self.parser.parse_credits(data)
                return credits_info
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed for provider {self.provider_name_value}",
                    provider=self.provider_name_value
                ) from e
            elif status_code == 429:
                raise RateLimitError(
                    f"Rate limit exceeded for provider {self.provider_name_value}",
                    provider=self.provider_name_value
                ) from e
            else:
                raise APIError(
                    f"API request failed with status {status_code} for provider {self.provider_name_value}",
                    status_code=status_code,
                    provider=self.provider_name_value
                ) from e
        except httpx.RequestError as e:
            raise NetworkError(
                f"Network error occurred for provider {self.provider_name_value}",
                original_error=e
            ) from e

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
        cache_ttl_hours: int = 1,
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
            cache_ttl_hours=cache_ttl_hours,
        )

    @staticmethod
    def create_openrouter(
        api_key: Optional[str] = None, cache_ttl_hours: int = 1
    ) -> GenericProvider:
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
            cache_ttl_hours=cache_ttl_hours,
        )
