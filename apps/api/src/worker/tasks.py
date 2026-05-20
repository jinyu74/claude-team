# Celery 태스크 정의 — dummy.sleep (M7/M8: DB 상태 전이 + 에러 마스킹)
import os
import time

from celery import Task
from celery.utils.log import get_task_logger

from src.extensions import db
from src.models.job import Job
from src.services.job import record_job_progress, transition_job
from src.worker.celery_app import celery

logger = get_task_logger(__name__)


class PermanentError(Exception):
    pass


class TransientError(Exception):
    pass


def _backoff_sec(retry_count: int) -> float:
    base = float(os.environ.get("CELERY_BACKOFF_BASE_SEC", "1"))
    return base * (4 ** retry_count)


def _mask(msg: str) -> str:
    return msg[:200]


@celery.task(
    name="dummy.sleep",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def dummy_sleep(
    self: Task,
    job_id: str,
    user_id: str,
    seconds: int = 5,
    fail: bool = False,
    transient: bool = False,
    progress: list[float] | None = None,
) -> dict:
    job = db.session.get(Job, job_id)
    if job is None or job.status == "canceled":
        return {"skipped": True}

    transition_job(job, "running")

    try:
        if transient:
            if self.request.retries < self.max_retries:
                raise self.retry(
                    exc=TransientError("transient failure"),
                    countdown=_backoff_sec(self.request.retries),
                )
            transition_job(job, "failed", error=_mask("transient error"))
            return {"failed": True}

        if fail:
            raise PermanentError("forced failure")

        if progress:
            segment = seconds / (len(progress) + 1)
            for pct in progress:
                time.sleep(segment)
                record_job_progress(job, user_id, pct)
            time.sleep(segment)
        else:
            time.sleep(seconds)

        transition_job(job, "succeeded")
        return {"slept": seconds}

    except PermanentError as exc:
        transition_job(job, "failed", error=_mask(str(exc)))
        return {"failed": True}
