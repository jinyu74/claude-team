# 잡 서비스 — 생성·상태 전환·Redis 발행
import uuid
from datetime import UTC, datetime

from src.extensions import db, get_redis
from src.models.job import JOB_STATUSES, Job, JobEvent
from src.services.sse import publish_job_event
from src.utils.idempotency import acquire_idempotency_lock

PAYLOAD_MAX_BYTES = 50_000

# ADR §5.4 이벤트별 허용 페이로드 키 (카탈로그)
_EVENT_PAYLOAD_KEYS: dict[str, tuple[str, ...]] = {
    "job.submitted": ("id", "type", "priority", "created_at"),
    "job.started":   ("id", "started_at", "attempts"),
    "job.succeeded": ("id", "finished_at"),
    "job.failed":    ("id", "finished_at", "error"),
    "job.canceled":  ("id", "finished_at"),
    "job.retried":   ("id", "retried_to_job_id"),
    "job.progress":  ("id", "percent", "at"),
}

# DB 상태명 → SSE 이벤트명 (ADR §5.4 명칭 준수)
_STATUS_TO_EVENT: dict[str, str] = {
    "running":   "job.started",
    "succeeded": "job.succeeded",
    "failed":    "job.failed",
    "canceled":  "job.canceled",
}


class ConflictError(Exception):
    """Idempotency 키 경합 — 동시 요청이 INSERT 중."""


def _now() -> datetime:
    return datetime.now(UTC)


def _event_payload(event_type: str, job: Job) -> dict:
    """ADR §5.4 카탈로그에 따라 이벤트별 허용 키만 추출한다."""
    keys = _EVENT_PAYLOAD_KEYS.get(event_type, ("id",))
    full = job.to_dict()
    return {k: full[k] for k in keys if k in full}


def _record_event(job: Job, user_id: str, event_type: str, event_data: dict) -> None:
    """publish_job_event 호출 후 job_events 행을 기록한다."""
    r = get_redis()
    ulid = publish_job_event(r, user_id, job.id, event_type, event_data)
    db.session.add(JobEvent(job_id=job.id, user_id=user_id, type=event_type, payload=event_data, event_ulid=ulid))  # type: ignore[call-arg]  # noqa: E501
    db.session.commit()


def create_job(
    user_id: str,
    job_type: str,
    payload: dict,
    priority: int,
    idempotency_key: str,
) -> tuple[Job, bool]:
    """잡을 생성한다. (job, created) — created=False 면 기존 잡 반환."""
    r = get_redis()
    if not acquire_idempotency_lock(r, user_id, idempotency_key):
        existing = Job.query.filter_by(user_id=user_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
        # lock 실패 + DB 미존재 → 동시 INSERT 경합 중 (H2)
        raise ConflictError("concurrent submission on the same idempotency key")

    job = Job(id=str(uuid.uuid4()), user_id=user_id, type=job_type, payload=payload, priority=priority, idempotency_key=idempotency_key, status="pending")  # type: ignore[call-arg]  # noqa: E501
    db.session.add(job)
    db.session.commit()

    event_type = "job.submitted"  # C3: job.created → job.submitted
    _record_event(job, user_id, event_type, _event_payload(event_type, job))
    return job, True


def transition_job(job: Job, new_status: str, **kwargs) -> Job:
    """잡 상태를 전환하고 SSE 이벤트를 발행한다."""
    if new_status not in JOB_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    job.status = new_status
    if new_status == "running":
        job.started_at = _now()
        job.attempts = (job.attempts or 0) + 1
    elif new_status in ("succeeded", "failed", "canceled"):
        job.finished_at = _now()

    for k, v in kwargs.items():
        setattr(job, k, v)

    db.session.commit()

    event_type = _STATUS_TO_EVENT.get(new_status, f"job.{new_status}")  # C4: running → job.started
    _record_event(job, job.user_id, event_type, _event_payload(event_type, job))
    return job
