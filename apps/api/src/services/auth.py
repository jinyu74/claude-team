# 인증 서비스 — 세션 생성·조회·폐기, argon2id 비밀번호 해시
import secrets

import redis as redis_lib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

SESSION_TTL = 1_209_600  # 14일 (초)
SESSION_PREFIX = "sid:"
USER_SIDS_PREFIX = "user_sids:"


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False


def create_session(r: redis_lib.Redis, user_id: str) -> str:
    sid = secrets.token_urlsafe(32)
    key = f"{SESSION_PREFIX}{sid}"
    r.hset(key, mapping={"user_id": user_id})
    r.expire(key, SESSION_TTL)
    r.sadd(f"{USER_SIDS_PREFIX}{user_id}", sid)
    return sid


def get_session(r: redis_lib.Redis, sid: str) -> str | None:
    key = f"{SESSION_PREFIX}{sid}"
    user_id = r.hget(key, "user_id")
    if user_id is None:
        return None
    r.expire(key, SESSION_TTL)
    return user_id.decode() if isinstance(user_id, bytes) else user_id  # type: ignore[return-value]


def revoke_session(r: redis_lib.Redis, sid: str, user_id: str) -> None:
    r.delete(f"{SESSION_PREFIX}{sid}")
    r.srem(f"{USER_SIDS_PREFIX}{user_id}", sid)


def revoke_all_for(r: redis_lib.Redis, user_id: str) -> None:
    sids_key = f"{USER_SIDS_PREFIX}{user_id}"
    sids = r.smembers(sids_key)
    if sids:
        r.delete(*(f"{SESSION_PREFIX}{s.decode() if isinstance(s, bytes) else s}" for s in sids))  # type: ignore[union-attr]
    r.delete(sids_key)
