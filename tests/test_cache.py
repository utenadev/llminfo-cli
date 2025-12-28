"""Tests for cache functionality"""

import pytest
from datetime import datetime, timedelta

from llminfo_cli.cache import CacheManager
from llminfo_cli.schemas import ModelInfo


@pytest.fixture
def cache_manager():
    manager = CacheManager()
    yield manager
    cache_file = manager.CACHE_DIR / "test_provider_models.json"
    if cache_file.exists():
        cache_file.unlink()


@pytest.mark.asyncio
async def test_cache_set_and_get(cache_manager):
    """Test setting and getting cache"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=1000, pricing=None),
        ModelInfo(id="model2", name="Model 2", context_length=2000, pricing=None),
    ]

    cache_manager.set("test_provider", models)
    cached_models = cache_manager.get("test_provider")

    assert cached_models is not None
    assert len(cached_models) == 2
    assert cached_models[0].id == "model1"
    assert cached_models[1].id == "model2"


def test_cache_expiration(cache_manager):
    """Test cache expiration after TTL"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=1000),
    ]

    cache_manager.set("test_provider", models)

    cache_file = cache_manager._get_cache_file("test_provider")
    with cache_file.open() as f:
        import json

        cache_data = json.load(f)

    expired_time = datetime.now() - timedelta(hours=2)
    cache_data["cached_at"] = expired_time.isoformat()

    with cache_file.open("w") as f:
        json.dump(cache_data, f)

    cached_models = cache_manager.get("test_provider")
    assert cached_models is None


def test_cache_invalidate(cache_manager):
    """Test cache invalidation"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=1000),
    ]

    cache_manager.set("test_provider", models)
    assert cache_manager.get("test_provider") is not None

    cache_manager.invalidate("test_provider")
    assert cache_manager.get("test_provider") is None
