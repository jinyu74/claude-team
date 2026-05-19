# 전역 확장 객체 — SQLAlchemy, Redis 클라이언트
import redis as redis_lib
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

_redis_client: redis_lib.Redis | None = None


def init_redis(url: str) -> redis_lib.Redis:
    global _redis_client
    _redis_client = redis_lib.Redis.from_url(url, decode_responses=True)
    return _redis_client


def get_redis() -> redis_lib.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis first.")
    return _redis_client
