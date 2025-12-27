"""OpenRouter provider implementation"""

import os
from typing import List, Optional

import httpx

from llminfo_cli.providers.base import Provider
from llminfo_cli.schemas import CreditInfo, ModelInfo


class OpenRouterProvider(Provider):
    """OpenRouter.ai provider implementation"""

    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_ENV = "OPENROUTER_API_KEY"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(self.API_KEY_ENV)

    async def get_models(self) -> List[ModelInfo]:
        """Fetch list of available models from OpenRouter"""
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

            return [
                ModelInfo(
                    id=m["id"],
                    name=m["name"],
                    context_length=m.get("context_length"),
                    pricing=m.get("pricing"),
                    is_free=":free" in m["id"],
                )
                for m in data
            ]

    async def get_credits(self) -> Optional[CreditInfo]:
        """Fetch credit information from OpenRouter"""
        if not self.api_key:
            raise ValueError(f"{self.API_KEY_ENV} environment variable not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/credits",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()["data"]

            total_credits = data.get("total_credits", 0.0)
            total_usage = data.get("total_usage", 0.0)

            return CreditInfo(
                total_credits=total_credits,
                usage=total_usage,
                remaining=total_credits - total_usage,
            )

    @property
    def provider_name(self) -> str:
        """Provider name"""
        return "openrouter"
