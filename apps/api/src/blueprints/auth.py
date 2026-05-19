# 인증 블루프린트 — POST /api/auth/login, POST /api/auth/logout, GET /api/me
from flask import Blueprint, g, jsonify, make_response, request

from src.extensions import db, get_redis
from src.middleware.csrf import generate_csrf_token
from src.middleware.session import require_auth
from src.models.user import User
from src.services.auth import create_session, revoke_session, verify_password

bp = Blueprint("auth", __name__, url_prefix="/api")

SESSION_COOKIE_NAME = "sid"


@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 422

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    r = get_redis()
    sid = create_session(r, user.id)
    csrf_token = generate_csrf_token(r, sid)

    resp = make_response(jsonify({"user": user.to_dict(), "csrf_token": csrf_token}), 200)
    resp.set_cookie(
        SESSION_COOKIE_NAME,
        sid,
        httponly=True,
        samesite="Lax",
        secure=False,  # 프로덕션에서는 True — Config.SESSION_COOKIE_SECURE 로 제어
        max_age=1_209_600,
    )
    return resp


@bp.route("/auth/logout", methods=["POST"])
@require_auth
def logout():
    r = get_redis()
    sid = g.get("sid")
    if sid:
        revoke_session(r, sid, g.current_user_id)
    resp = make_response("", 204)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp


@bp.route("/me", methods=["GET"])
@require_auth
def me():
    user = db.session.get(User, g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
