import time
from unittest.mock import patch
from app.core.search_cache import (
    get_cached_search,
    invalidate_cache,
    make_cache_key,
    set_cached_search,
)


@patch("app.core.search_cache._get_mongo_collection", return_value=None)
def test_make_cache_key_deterministic(mock_mongo):
    key1 = make_cache_key("test_type", "query 1", 10)
    key2 = make_cache_key("test_type", "query 1", 10)
    key3 = make_cache_key("test_type", "query 2", 10)

    assert key1 == key2
    assert key1 != key3


@patch("app.core.search_cache._get_mongo_collection", return_value=None)
def test_set_and_get_cached_search(mock_mongo):
    cache_type = "test_unit"
    key = make_cache_key("sample_query")
    sample_data = [{"name": "Test Scholarship", "amount": 50000}]

    invalidate_cache(cache_type, key)

    # Initial check should be None
    assert get_cached_search(cache_type, key) is None

    # Set cache with 5s TTL
    set_cached_search(cache_type, key, sample_data, ttl_seconds=5)

    cached = get_cached_search(cache_type, key)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0]["name"] == "Test Scholarship"

    # Invalidate and check
    invalidate_cache(cache_type, key)
    assert get_cached_search(cache_type, key) is None


@patch("app.core.search_cache._get_mongo_collection", return_value=None)
def test_cache_expiration(mock_mongo):
    cache_type = "test_unit_expire"
    key = make_cache_key("expire_query")
    sample_data = {"test": 123}

    # Set cache with 1s TTL
    set_cached_search(cache_type, key, sample_data, ttl_seconds=1)
    assert get_cached_search(cache_type, key) == sample_data

    # Sleep past expiration
    time.sleep(1.2)
    assert get_cached_search(cache_type, key) is None
