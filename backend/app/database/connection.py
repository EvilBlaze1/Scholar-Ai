import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "scholar_ai")


if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not configured")


client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

database = client[MONGODB_DB]