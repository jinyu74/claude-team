# 잡 블루프린트 — ADR §5.1 엔드포인트 구현
import functools
import uuid

from flask import Blueprint, g, jsonify, request

from src.extensions import db, get_redis
from src.middleware.csrf import validate_csrf_token
from src.middleware.session import require_auth
from src.models.job import Job
from src.services.job import ConflictError, create_job, transition_job

# 테스트에서 src.blueprints.jobs.submit_job_task 로 패치 가능
from src.worker.celery_app import celery as celery_app
from src.worker.tasks import dummy_sleep as submit_job_task  # noqa: E402

bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100

# H4: apply_async 에 허용하는 kwargs 키 목록
_TASK_KWARGS_WHITELIST = frozenset(["seconds", "fail", "transient", "progress"])


def _err(code: str, message: str) -> dict:
    """ADR §5.5 오류 봉투."""
    return {"error": {"code": code, "message": message}}


def require_csrf(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        r = get_redis()
        sid = g.get("sid", "")
        token = request.headers.get("X-CSRF-Token", "")
        if not validate_csrf_token(r, sid, token):
            return jsonify(_err("CSRF_FAILED", "CSRF token invalid")), 403
        return f(*args, **kwargs)
    return wrapper


@bp.route("", methods=["POST"])
@require_auth
@require_csrf
def submit_job():
    data = request.get_json(silent=True) or {}
    job_type = data.get("type", "").strip()
    if not job_type:
        return jsonify(_err("VALIDATION_FAILED", "type is required")), 422

    payload = data.get("payload", {}) or {}
    priority = int(data.get("priority", 0))
    idempotency_key = (
        request.headers.get("Idempotency-Key") or data.get("idempotency_key", "")
    )
    if not idempotency_key:
        return jsonify(_err("VALIDATION_FAILED", "Idempotency-Key required")), 422

    try:
        job, created = create_job(
            user_id=g.current_user_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            idempotency_key=idempotency_key,
        )
    except ConflictError:
        return (
            jsonify(_err("IDEMPOTENCY_CONFLICT", "concurrent submission detected, retry shortly")),
            409,
        )

    if created:
        queue = "high" if priority > 0 else "default"
        # H4: 사용자 페이로드를 whitelist 로 필터링 후 전달
        safe_kwargs = {k: v for k, v in payload.items() if k in _TASK_KWARGS_WHITELIST}
        result = submit_job_task.apply_async(kwargs={"job_id": job.id, "user_id": job.user_id, **safe_kwargs}, queue=queue)  # type: ignore[union-attr]
        job.celery_task_id = result.id
        db.session.commit()

    status = 201 if created else 200
    return jsonify(job.to_dict()), status


@bp.route("", methods=["GET"])
@require_auth
def list_jobs():
    status_filter = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(PAGE_SIZE_MAX, int(request.args.get("per_page", PAGE_SIZE_DEFAULT)))

    q = Job.query.filter_by(user_id=g.current_user_id)
    if status_filter:
        q = q.filter_by(status=status_filter)
    q = q.order_by(Job.created_at.desc())  # type: ignore[union-attr]

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "items": [j.to_dict() for j in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@bp.route("/<job_id>", methods=["GET"])
@require_auth
def get_job(job_id: str):
    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return jsonify(_err("NOT_FOUND", "Not found")), 404
    return jsonify(job.to_dict()), 200


@bp.route("/<job_id>", methods=["PATCH"])
@require_auth
@require_csrf
def update_job(job_id: str):
    """ADR §5.1: 취소 = {status: "canceled"}, 재시도 = {action: "retry"}."""
    data = request.get_json(silent=True) or {}

    job = Job.query.filter_by(id=job_id, user_id=g.current_user_id).first()
    if not job:
        return jsonify(_err("NOT_FOUND", "Not found")), 404

    # H1: {status: "canceled"} — ADR §5.1 준수
    if data.get("status") == "canceled":
        if job.status not in ("pending", "running"):
            return (
                jsonify(_err("INVALID_TRANSITION", f"Cannot cancel job in status '{job.status}'")),
                409,
            )
        if job.celery_task_id:
            celery_app.control.revoke(job.celery_task_id, terminate=True)
        job = transition_job(job, "canceled")
        return jsonify(job.to_dict()), 200

    if data.get("action") == "retry":
        if job.status == "succeeded":
            return jsonify(_err("INVALID_TRANSITION", "retry not allowed from succeeded")), 409
        if job.status in ("pending", "running"):
            return jsonify(_err("INVALID_TRANSITION", "job not finalized")), 409
        # failed | canceled → 새 job 생성
        new_job, _ = create_job(
            user_id=g.current_user_id,
            job_type=job.type,
            payload=job.payload,
            priority=job.priority,
            idempotency_key=str(uuid.uuid4()),
        )
        job.retried_to_job_id = new_job.id
        db.session.commit()
        safe_kwargs = {
            k: v for k, v in (new_job.payload or {}).items() if k in _TASK_KWARGS_WHITELIST
        }
        result = submit_job_task.apply_async(kwargs={"job_id": new_job.id, "user_id": new_job.user_id, **safe_kwargs}, queue="default")  # type: ignore[union-attr]
        new_job.celery_task_id = result.id
        db.session.commit()
        return jsonify(new_job.to_dict()), 201

    return jsonify(_err("VALIDATION_FAILED", "unknown action")), 422
