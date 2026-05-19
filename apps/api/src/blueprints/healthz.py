# 헬스체크 엔드포인트 — GET /healthz
from flask import Blueprint, jsonify
from src.extensions import db, get_redis

bp = Blueprint("healthz", __name__)


@bp.route("/healthz", methods=["GET"])
def healthz():
    try:
        db.session.execute(db.text("SELECT 1"))
        get_redis().ping()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 503
