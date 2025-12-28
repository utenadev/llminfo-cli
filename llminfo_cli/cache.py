"""Cache management for provider models"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from llminfo_cli.schemas import ModelInfo


class CacheManager:
    """Manage provider model caches"""

    CACHE_DIR = Path.home() / ".cache" / "llminfo"
    CACHE_TTL = timedelta(hours=1)

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, provider_name: str) -> Path:
        """Get cache file path for provider"""
        return self.CACHE_DIR / f"{provider_name}_models.json"

    def get(self, provider_name: str) -> Optional[List[ModelInfo]]:
        """Get cached models if valid"""
        cache_file = self._get_cache_file(provider_name)

        if not cache_file.exists():
            return None

        with cache_file.open() as f:
            cache_data = json.load(f)

        cached_at = datetime.fromisoformat(cache_data["cached_at"])
        if datetime.now() - cached_at > self.CACHE_TTL:
            return None

        return [ModelInfo(**m) for m in cache_data["models"]]

    def set(self, provider_name: str, models: List[ModelInfo]) -> None:
        """Cache models for provider"""
        cache_file = self._get_cache_file(provider_name)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "provider": provider_name,
            "models": [m.model_dump() for m in models],
        }

        with cache_file.open("w") as f:
            json.dump(cache_data, f, indent=2)

    def invalidate(self, provider_name: str) -> None:
        """Invalidate cache for provider"""
        cache_file = self._get_cache_file(provider_name)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                pass
