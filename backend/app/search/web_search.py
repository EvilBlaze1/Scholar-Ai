import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_URL = "https://google.serper.dev/search"


def search_web(query: str, num_results: int = 10):
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

    return results