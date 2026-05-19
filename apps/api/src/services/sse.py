# SSE 이벤트 직렬화·구독·백필 서비스 — ADR §6
import json
import time

import redis as redis_lib
from ulid import ULID

from src.utils.emit_timing import maybe_add_emit_at

STREAM_KEY_JOBS = "stream:events:jobs"
STREAM_KEY_JOB = "stream:events:job:{job_id}"
STREAM_MAXLEN = 10_000
STREAM_BACKFILL_MAX = 100
STREAM_BACKFILL_AGE = 60  # 초

# ADR §5.4 채널 라우팅 — 라이프사이클 이벤트는 user 채널 전용
_USER_ONLY_EVENTS = frozenset([
    "job.submitted", "job.started", "job.succeeded",
    "job.failed", "job.canceled", "job.retried",
])
# log_line 은 job 상세 채널 전용
_JOB_ONLY_EVENTS = frozenset(["log_line"])
# job.progress: user 채널 1s throttle + job 채널 raw
_PROGRESS_THROTTLE_KEY = "throttle:progress:{user_id}:{job_id}"


def format_sse_event(event_type: str, data: dict, event_id: str | None = None) -> str:
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def format_keepalive() -> str:
    return ": ping\n\n"


def publish_job_event(
    r: redis_lib.Redis,
    user_id: str,
    job_id: str,
    event_type: str,
    data: dict,
) -> str:
    ulid = str(ULID())
    data = maybe_add_emit_at(data)
    payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)

    pipe = r.pipeline()

    if event_type in _USER_ONLY_EVENTS:
        pipe.publish(f"events:jobs:user:{user_id}", payload)
    elif event_type in _JOB_ONLY_EVENTS:
        pipe.publish(f"events:jobs:job:{job_id}", payload)
    elif event_type == "job.progress":
        # job 채널: 무조건 발행 (raw)
        pipe.publish(f"events:jobs:job:{job_id}", payload)
        # user 채널: 1s throttle — pipeline 외부에서 원자적 SET NX 확인
        throttle_key = _PROGRESS_THROTTLE_KEY.format(user_id=user_id, job_id=job_id)
        if r.set(throttle_key, 1, ex=1, nx=True):
            pipe.publish(f"events:jobs:user:{user_id}", payload)
    else:
        # 미분류 이벤트 → user 채널
        pipe.publish(f"events:jobs:user:{user_id}", payload)

    # Redis Stream 에 기록 (백필용)
    entry = {
        "ulid": ulid, "type": event_type, "data": payload,
        "user_id": user_id, "job_id": job_id,
    }
    pipe.xadd(STREAM_KEY_JOBS, entry, maxlen=STREAM_MAXLEN, approximate=True)  # type: ignore[arg-type]
    pipe.xadd(STREAM_KEY_JOB.format(job_id=job_id), entry, maxlen=500, approximate=True)  # type: ignore[arg-type]
    pipe.execute()
    return ulid


def backfill_from_stream(
    r: redis_lib.Redis,
    last_event_id: str,
    user_id: str,
    job_id: str | None = None,
) -> list[str]:
    """Last-Event-ID 이후 이벤트를 Redis Stream 에서 읽어 SSE 문자열 리스트로 반환."""
    stream_key = STREAM_KEY_JOB.format(job_id=job_id) if job_id else STREAM_KEY_JOBS
    cutoff_ts = (time.time() - STREAM_BACKFILL_AGE) * 1000

    try:
        entries = r.xrange(stream_key, min=last_event_id, count=STREAM_BACKFILL_MAX)
    except Exception:
        return []

    result = []
    for stream_id, fields in entries:  # type: ignore[union-attr]
        if stream_id.decode() == last_event_id:
            continue
        ts_part = int(stream_id.decode().split("-")[0])
        if ts_part < cutoff_ts:
            continue
        uid = fields.get(b"user_id", b"").decode()
        if job_id is None and uid != user_id:
            continue
        event_type = fields.get(b"type", b"unknown").decode()
        raw_data = fields.get(b"data", b"{}").decode()
        try:
            inner = json.loads(raw_data)
            data = inner.get("data", {}) if isinstance(inner, dict) else {}
        except json.JSONDecodeError:
            data = {}
        ulid = fields.get(b"ulid", b"").decode()
        result.append(format_sse_event(event_type, data, event_id=ulid))
    return result
