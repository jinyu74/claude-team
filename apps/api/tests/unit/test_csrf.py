# CSRF 토큰 단위 테스트 — 생성·검증·불일치
import pytest


class TestCSRFToken:
    def test_generate_csrf_token_returns_string(self, fake_redis):
        from src.middleware.csrf import generate_csrf_token
        token = generate_csrf_token(fake_redis, sid="test-sid-1")
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_csrf_token_stored_in_redis(self, fake_redis):
        from src.middleware.csrf import generate_csrf_token
        token = generate_csrf_token(fake_redis, sid="test-sid-2")
        stored = fake_redis.get("csrf:test-sid-2")
        assert stored == token

    def test_validate_correct_csrf_token(self, fake_redis):
        from src.middleware.csrf import generate_csrf_token, validate_csrf_token
        token = generate_csrf_token(fake_redis, sid="test-sid-3")
        assert validate_csrf_token(fake_redis, sid="test-sid-3", token=token) is True

    def test_validate_wrong_csrf_token(self, fake_redis):
        from src.middleware.csrf import generate_csrf_token, validate_csrf_token
        generate_csrf_token(fake_redis, sid="test-sid-4")
        assert validate_csrf_token(fake_redis, sid="test-sid-4", token="wrong-token") is False

    def test_validate_missing_csrf_token(self, fake_redis):
        from src.middleware.csrf import validate_csrf_token
        assert validate_csrf_token(fake_redis, sid="no-session", token="any") is False
