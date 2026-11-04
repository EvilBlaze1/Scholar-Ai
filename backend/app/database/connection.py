import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "scholar_ai")


if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not configured")


_mongo_options = {
    "serverSelectionTimeoutMS": 5000,
}
try:
    import certifi
    _mongo_options["tlsCAFile"] = certifi.where()
except Exception:
    pass

try:
    client = MongoClient(
        MONGODB_URI,
        **_mongo_options
    )
    database = client[MONGODB_DB]
except Exception as exc:
    logging.warning(
        "Could not connect to MongoDB URI (%s). Falling back to deferred connection.",
        exc,
    )
    try:
        client = MongoClient(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=100,
        )
        database = client[MONGODB_DB]
    except Exception:
        class _FallbackCollection:
            def __getattr__(self, name):
                return lambda *args, **kwargs: None

        class _FallbackDatabase:
            def __getitem__(self, name):
                return _FallbackCollection()

        client = None
        database = _FallbackDatabase()