# 세션 검증 미들웨어 — before_request 훅 + require_auth 데코레이터
import functools

from flask import g, jsonify, request

from src.extensions import get_redis
from src.services.auth import get_session


def load_session() -> None:
    """모든 요청 전 sid 쿠키로 세션을 로드한다."""
    g.current_user_id = None
    sid = request.cookies.get("sid")
    if sid:
        r = get_redis()
        user_id = get_session(r, sid)
        if user_id:
            g.current_user_id = user_id
            g.sid = sid


def require_auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not g.get("current_user_id"):
            body = {"error": {"code": "UNAUTHENTICATED", "message": "authentication required"}}
            return jsonify(body), 401
        return f(*args, **kwargs)
    return wrapper
