# 멱등성 키 락 — Redis SET NX EX 60s
import redis as redis_lib

IDEMPOTENCY_TTL = 60


def acquire_idempotency_lock(r: redis_lib.Redis, user_id: str, key: str) -> bool:
    """60초 멱등성 락을 획득한다. 이미 존재하면 False."""
    redis_key = f"idem:{user_id}:{key}"
    return bool(r.set(redis_key, "1", ex=IDEMPOTENCY_TTL, nx=True))
