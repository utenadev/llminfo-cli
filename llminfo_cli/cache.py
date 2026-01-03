"""Cache management for provider models"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import aiofiles

from llminfo_cli.schemas import ModelInfo


class CacheManager:
    """Manage provider model caches"""

    CACHE_DIR = Path.home() / ".cache" / "llminfo"
    DEFAULT_CACHE_TTL = timedelta(hours=1)

    def __init__(self, ttl_hours: int = 1):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_TTL = timedelta(hours=ttl_hours)

    def _get_cache_file(self, provider_name: str) -> Path:
        """Get cache file path for provider"""
        return self.CACHE_DIR / f"{provider_name}_models.json"

    async def get(self, provider_name: str) -> Optional[List[ModelInfo]]:
        """Get cached models if valid"""
        cache_file = self._get_cache_file(provider_name)

        if not cache_file.exists():
            return None

        async with aiofiles.open(cache_file, 'r') as f:
            cache_content = await f.read()
            cache_data = json.loads(cache_content)

        cached_at = datetime.fromisoformat(cache_data["cached_at"])
        if datetime.now() - cached_at > self.CACHE_TTL:
            return None

        return [ModelInfo(**m) for m in cache_data["models"]]

    async def set(self, provider_name: str, models: List[ModelInfo]) -> None:
        """Cache models for provider"""
        cache_file = self._get_cache_file(provider_name)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "provider": provider_name,
            "models": [m.model_dump() for m in models],
        }

        async with aiofiles.open(cache_file, 'w') as f:
            await f.write(json.dumps(cache_data, indent=2))

    async def invalidate(self, provider_name: str) -> None:
        """Invalidate cache for provider"""
        cache_file = self._get_cache_file(provider_name)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                pass
