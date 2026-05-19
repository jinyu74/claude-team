# 인증 유틸 단위 테스트 — 해시·검증·세션 생성
import pytest


class TestPasswordHashing:
    def test_hash_returns_argon2id_string(self):
        from src.services.auth import hash_password
        result = hash_password("my-secret-password")
        assert result.startswith("$argon2id$")

    def test_verify_correct_password(self):
        from src.services.auth import hash_password, verify_password
        hashed = hash_password("correct-password")
        assert verify_password("correct-password", hashed) is True

    def test_verify_wrong_password(self):
        from src.services.auth import hash_password, verify_password
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_unique_per_call(self):
        from src.services.auth import hash_password
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2  # argon2 uses random salt


class TestSessionManagement:
    def test_create_session_returns_sid(self, fake_redis):
        from src.services.auth import create_session
        sid = create_session(fake_redis, user_id="user-uuid-1")
        assert sid is not None
        assert len(sid) > 16

    def test_session_stored_in_redis(self, fake_redis):
        from src.services.auth import create_session
        sid = create_session(fake_redis, user_id="user-uuid-1")
        stored = fake_redis.hget(f"sid:{sid}", "user_id")
        assert stored == "user-uuid-1"

    def test_session_has_ttl(self, fake_redis):
        from src.services.auth import create_session
        sid = create_session(fake_redis, user_id="user-uuid-1")
        ttl = fake_redis.ttl(f"sid:{sid}")
        assert ttl > 0

    def test_get_session_returns_user_id(self, fake_redis):
        from src.services.auth import create_session, get_session
        sid = create_session(fake_redis, user_id="user-uuid-2")
        user_id = get_session(fake_redis, sid)
        assert user_id == "user-uuid-2"

    def test_get_session_returns_none_for_unknown_sid(self, fake_redis):
        from src.services.auth import get_session
        result = get_session(fake_redis, "nonexistent-sid")
        assert result is None

    def test_revoke_session_removes_from_redis(self, fake_redis):
        from src.services.auth import create_session, revoke_session, get_session
        sid = create_session(fake_redis, user_id="user-uuid-3")
        revoke_session(fake_redis, sid, user_id="user-uuid-3")
        assert get_session(fake_redis, sid) is None

    def test_revoke_all_sessions_for_user(self, fake_redis):
        from src.services.auth import create_session, revoke_all_for, get_session
        sid1 = create_session(fake_redis, user_id="user-uuid-4")
        sid2 = create_session(fake_redis, user_id="user-uuid-4")
        revoke_all_for(fake_redis, user_id="user-uuid-4")
        assert get_session(fake_redis, sid1) is None
        assert get_session(fake_redis, sid2) is None
