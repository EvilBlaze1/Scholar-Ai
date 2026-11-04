import logging
import os
import requests
from dotenv import load_dotenv

from app.core.search_cache import get_cached_search, make_cache_key, set_cached_search

logger = logging.getLogger(__name__)

load_dotenv()

SERPER_API_URL = "https://google.serper.dev/search"


def search_web(query: str, num_results: int = 10, use_cache: bool = True):
    cache_key = make_cache_key("serper_web", query.strip().lower(), num_results)

    if use_cache:
        cached = get_cached_search("web_search", cache_key)
        if cached is not None and isinstance(cached, list):
            logger.info("Search cache hit for query=%r (results=%d)", query.strip(), len(cached))
            return cached

    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        raise ValueError("SERPER_API_KEY is not configured")

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "gl": "in",
        "hl": "en",
        "num": num_results,
    }

    response = requests.post(
        SERPER_API_URL,
        headers=headers,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("organic", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "description": item.get("snippet"),
        })

    # Cache for 2 hours (7200 seconds)
    if use_cache and results:
        set_cached_search("web_search", cache_key, results, ttl_seconds=7200)

    return results
