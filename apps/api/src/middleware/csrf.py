# CSRF 토큰 생성·검증 미들웨어 — double-submit 패턴
import secrets

import redis as redis_lib

CSRF_PREFIX = "csrf:"
CSRF_TTL = 1_209_600  # 세션과 동일 14일


def generate_csrf_token(r: redis_lib.Redis, sid: str) -> str:
    token = secrets.token_urlsafe(32)
    r.set(f"{CSRF_PREFIX}{sid}", token, ex=CSRF_TTL)
    return token


def validate_csrf_token(r: redis_lib.Redis, sid: str, token: str) -> bool:
    stored = r.get(f"{CSRF_PREFIX}{sid}")
    if stored is None or not token:
        return False
    stored_str = stored.decode() if isinstance(stored, bytes) else stored
    return secrets.compare_digest(stored_str, token)  # type: ignore[arg-type]
