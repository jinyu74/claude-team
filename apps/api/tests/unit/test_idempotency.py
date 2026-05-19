# 멱등성 키 단위 테스트 — 락 획득·중복 방지
import pytest


class TestIdempotencyLock:
    def test_acquire_lock_succeeds_first_time(self, fake_redis):
        from src.utils.idempotency import acquire_idempotency_lock
        acquired = acquire_idempotency_lock(fake_redis, user_id="u1", key="key-1")
        assert acquired is True

    def test_acquire_lock_fails_on_duplicate(self, fake_redis):
        from src.utils.idempotency import acquire_idempotency_lock
        acquire_idempotency_lock(fake_redis, user_id="u1", key="key-2")
        acquired_again = acquire_idempotency_lock(fake_redis, user_id="u1", key="key-2")
        assert acquired_again is False

    def test_different_users_same_key_both_succeed(self, fake_redis):
        from src.utils.idempotency import acquire_idempotency_lock
        ok1 = acquire_idempotency_lock(fake_redis, user_id="u1", key="shared-key")
        ok2 = acquire_idempotency_lock(fake_redis, user_id="u2", key="shared-key")
        assert ok1 is True
        assert ok2 is True

    def test_lock_has_60s_ttl(self, fake_redis):
        from src.utils.idempotency import acquire_idempotency_lock
        acquire_idempotency_lock(fake_redis, user_id="u1", key="key-3")
        ttl = fake_redis.ttl("idem:u1:key-3")
        assert 55 <= ttl <= 60
