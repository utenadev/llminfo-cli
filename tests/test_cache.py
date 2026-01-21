"""Tests for cache functionality"""

import pytest
from datetime import datetime, timedelta

import aiofiles

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

    await cache_manager.set("test_provider", models)
    cached_models = await cache_manager.get("test_provider")

    assert cached_models is not None
    assert len(cached_models) == 2
    assert cached_models[0].id == "model1"
    assert cached_models[1].id == "model2"


@pytest.mark.asyncio
async def test_cache_expiration(cache_manager):
    """Test cache expiration after TTL"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=1000),
    ]

    await cache_manager.set("test_provider", models)

    cache_file = cache_manager._get_cache_file("test_provider")
    async with aiofiles.open(cache_file, "r") as f:
        import json

        cache_content = await f.read()
        cache_data = json.loads(cache_content)

    expired_time = datetime.now() - timedelta(hours=2)
    cache_data["cached_at"] = expired_time.isoformat()

    async with aiofiles.open(cache_file, "w") as f:
        await f.write(json.dumps(cache_data))

    cached_models = await cache_manager.get("test_provider")
    assert cached_models is None


@pytest.mark.asyncio
async def test_cache_invalidate(cache_manager):
    """Test cache invalidation"""
    models = [
        ModelInfo(id="model1", name="Model 1", context_length=1000),
    ]

    await cache_manager.set("test_provider", models)
    assert await cache_manager.get("test_provider") is not None

    await cache_manager.invalidate("test_provider")
    assert await cache_manager.get("test_provider") is None
