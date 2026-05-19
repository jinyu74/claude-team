# SSE 이벤트 스트림 블루프린트 — /api/events/jobs, /api/events/jobs/:id
import time
import json
import redis as redis_lib
from flask import Blueprint, request, g, Response
from src.extensions import get_redis
from src.models.job import Job
from src.middleware.session import require_auth
from src.services.sse import format_sse_event, format_keepalive, backfill_from_stream
from src.utils.metrics import sse_clients_active, sse_messages_sent_total
from src.utils.emit_timing import strip_internal_keys, ENABLE_EMIT_AT

bp = Blueprint("events", __name__, url_prefix="/api/events")

KEEPALIVE_INTERVAL = 15  # 초


def subscribe_jobs_channel(
    r: redis_lib.Redis,
    channel: str,
    user_id: str,
    job_id: str | None = None,
    expose_emit_at: bool = False,
):
    """Redis pub/sub 채널 구독 제너레이터 — 테스트에서 패치 가능한 공개 함수."""
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    last_keepalive = time.time()
    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    raw = json.loads(message["data"])
                except (json.JSONDecodeError, TypeError):
                    continue
                event_type = raw.get("type", "unknown")
                data = strip_internal_keys(raw.get("data", {}), expose_emit_at=expose_emit_at)
                chunk = format_sse_event(event_type, data)
                sse_messages_sent_total.labels(event_type=event_type).inc()
                yield chunk

            now = time.time()
            if now - last_keepalive >= KEEPALIVE_INTERVAL:
                yield format_keepalive()
                last_keepalive = now
    finally:
        pubsub.unsubscribe()
        pubsub.close()


def _stream_channel(r: redis_lib.Redis, channel: str, user_id: str, job_id: str | None = None):
    """SSE 스트리밍 Response를 반환한다."""
    last_event_id = request.headers.get("Last-Event-ID")
    # H5: ADR §5.4.3 — 두 조건 모두 충족 시에만 _emit_at 클라이언트 노출
    expose_emit_at = ENABLE_EMIT_AT and request.headers.get("X-Perf-Client") == "test"

    def generate():
        sse_clients_active.inc()
        try:
            if last_event_id:
                for chunk in backfill_from_stream(r, last_event_id, user_id, job_id):
                    sse_messages_sent_total.labels(event_type="backfill").inc()
                    yield chunk

            for chunk in subscribe_jobs_channel(r, channel, user_id, job_id, expose_emit_at=expose_emit_at):
                yield chunk
        finally:
            sse_clients_active.dec()

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@bp.route("/jobs", methods=["GET"])
@require_auth
def jobs_stream():
    r = get_redis()
    channel = f"events:jobs:user:{g.current_user_id}"
    return _stream_channel(r, channel, g.current_user_id)


@bp.route("/jobs/<job_id>", methods=["GET"])
@require_auth
def job_detail_stream(job_id: str):
    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return {"error": "Not found"}, 404
    r = get_redis()
    channel = f"events:jobs:job:{job_id}"
    return _stream_channel(r, channel, g.current_user_id, job_id=job_id)
