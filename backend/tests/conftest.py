import os
import pytest

# Ensure offline test safety
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "test_scholar_ai")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-1234567890123456")
os.environ.setdefault("JWT_SECRET", "test-secret-key-1234567890123456")
