# 헬스체크 엔드포인트 — GET /healthz
from flask import Blueprint, jsonify

from src.extensions import get_redis

bp = Blueprint("healthz", __name__)


@bp.route("/healthz", methods=["GET"])
def healthz():
    try:
        get_redis().ping()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 503
