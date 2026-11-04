import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Fast in-memory cache: { "cache_type:key": {"expires_at": timestamp, "data": ...} }
_IN_MEMORY_CACHE: dict[str, dict[str, Any]] = {}
_INDEX_ENSURED = False
_MONGO_DISABLED_UNTIL = 0.0


def _mark_mongo_failed():
    """Circuit breaker: back off from MongoDB for 60s if unreachable."""
    global _MONGO_DISABLED_UNTIL
    _MONGO_DISABLED_UNTIL = time.time() + 60.0


def _get_mongo_collection():
    """Lazily load MongoDB search_cache collection with fallback."""
    global _MONGO_DISABLED_UNTIL
    if time.time() < _MONGO_DISABLED_UNTIL:
        return None

    try:
        from app.database.collections import search_cache_collection
        return search_cache_collection
    except Exception as exc:
        _mark_mongo_failed()
        logger.debug("MongoDB collection unavailable for caching: %s", exc)
        return None


def _ensure_mongo_index():
    """Ensure TTL and lookup indexes on the search_cache collection once."""
    global _INDEX_ENSURED
    if _INDEX_ENSURED:
        return

    collection = _get_mongo_collection()
    if collection is None:
        return

    try:
        collection.create_index(
            "expires_at",
            expireAfterSeconds=0,
            background=True,
        )
        collection.create_index(
            [("cache_type", 1), ("cache_key", 1)],
            unique=True,
            background=True,
        )
        _INDEX_ENSURED = True
    except Exception as exc:
        _mark_mongo_failed()
        logger.debug("Could not ensure search_cache mongo index: %s", exc)


def make_cache_key(*args: Any) -> str:
    """Create a deterministic hash string from variable arguments."""
    serialized = []
    for arg in args:
        if isinstance(arg, (dict, list)):
            serialized.append(json.dumps(arg, sort_keys=True, default=str))
        else:
            serialized.append(str(arg).strip().lower())

    combined = "||".join(serialized)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def get_cached_search(cache_type: str, key: str) -> Optional[Any]:
    """
    Retrieve cached search or evaluation results.
    Checks in-memory cache first, then MongoDB persistent cache.
    """
    mem_key = f"{cache_type}:{key}"
    now_ts = time.time()

    # 1. Check in-memory cache
    if mem_key in _IN_MEMORY_CACHE:
        entry = _IN_MEMORY_CACHE[mem_key]
        if now_ts < entry["expires_at"]:
            return entry["data"]
        else:
            del _IN_MEMORY_CACHE[mem_key]

    # 2. Check MongoDB collection
    collection = _get_mongo_collection()
    if collection is not None:
        try:
            now_dt = datetime.now(timezone.utc)
            record = collection.find_one({
                "cache_type": cache_type,
                "cache_key": key,
                "expires_at": {"$gt": now_dt},
            })

            if record and "data" in record:
                data = record["data"]
                # Populate in-memory cache with remaining TTL
                remaining_seconds = max(10, int((record["expires_at"] - now_dt).total_seconds()))
                _IN_MEMORY_CACHE[mem_key] = {
                    "expires_at": now_ts + remaining_seconds,
                    "data": data,
                }
                return data

        except Exception as exc:
            _mark_mongo_failed()
            logger.debug("Mongo cache lookup failed for %s:%s: %s", cache_type, key, exc)

    return None


def set_cached_search(
    cache_type: str,
    key: str,
    data: Any,
    ttl_seconds: int = 7200,
) -> None:
    """
    Store search or evaluation results in memory and MongoDB.
    Default TTL is 2 hours (7200 seconds).
    """
    if data is None:
        return

    mem_key = f"{cache_type}:{key}"
    now_ts = time.time()
    expires_ts = now_ts + ttl_seconds

    # 1. Write to in-memory cache
    _IN_MEMORY_CACHE[mem_key] = {
        "expires_at": expires_ts,
        "data": data,
    }

    # 2. Write to MongoDB if available
    collection = _get_mongo_collection()
    if collection is not None:
        try:
            _ensure_mongo_index()
            now_dt = datetime.now(timezone.utc)
            expires_dt = now_dt + timedelta(seconds=ttl_seconds)

            collection.update_one(
                {"cache_type": cache_type, "cache_key": key},
                {
                    "$set": {
                        "cache_type": cache_type,
                        "cache_key": key,
                        "data": data,
                        "expires_at": expires_dt,
                        "updated_at": now_dt,
                    },
                    "$setOnInsert": {
                        "created_at": now_dt,
                    },
                },
                upsert=True,
            )
        except Exception as exc:
            _mark_mongo_failed()
            logger.debug("Mongo cache store failed for %s:%s: %s", cache_type, key, exc)


def invalidate_cache(cache_type: Optional[str] = None, key: Optional[str] = None) -> None:
    """
    Invalidate entries matching cache_type and/or key.
    """
    global _IN_MEMORY_CACHE

    if cache_type and key:
        mem_key = f"{cache_type}:{key}"
        _IN_MEMORY_CACHE.pop(mem_key, None)
    elif cache_type:
        prefix = f"{cache_type}:"
        _IN_MEMORY_CACHE = {k: v for k, v in _IN_MEMORY_CACHE.items() if not k.startswith(prefix)}
    else:
        _IN_MEMORY_CACHE.clear()

    collection = _get_mongo_collection()
    if collection is not None:
        try:
            if cache_type and key:
                collection.delete_many({
                    "cache_type": cache_type,
                    "cache_key": key,
                })
            elif cache_type:
                collection.delete_many({"cache_type": cache_type})
            else:
                collection.delete_many({})
        except Exception:
            pass
