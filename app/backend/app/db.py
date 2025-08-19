from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from pymongo import MongoClient
from pymongo.collection import Collection

from .config import get_settings


_client: MongoClient | None = None


def get_mongo() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongo_url)
    return _client


def get_db():  # type: ignore[no-untyped-def]
    client = get_mongo()
    return client[get_settings().mongo_db]


def create_indexes() -> None:
    db = get_db()
    db["datasets"].create_index("uploaded_at")
    db["claims"].create_index([("dataset_id", 1), ("claim_id", 1), ("source_system", 1)], unique=True)
    db["rejections"].create_index("dataset_id")



