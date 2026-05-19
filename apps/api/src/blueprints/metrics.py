# Prometheus 메트릭 엔드포인트 — GET /metrics
from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

bp = Blueprint("metrics", __name__)


@bp.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
