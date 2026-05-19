# Celery 태스크 정의 — dummy.sleep (테스트용 장시간 작업)
import time
import random
from celery import Task
from celery.utils.log import get_task_logger
from src.worker.celery_app import celery

logger = get_task_logger(__name__)


class TransientError(Exception):
    pass


@celery.task(
    name="dummy.sleep",
    bind=True,
    max_retries=3,
    autoretry_for=(TransientError,),
    retry_backoff=True,
    retry_backoff_max=60,
    acks_late=True,
)
def dummy_sleep(self: Task, seconds: int = 5, fail_prob: float = 0.0) -> dict:
    """지정된 초만큼 대기하고 결과를 반환한다. fail_prob 확률로 일시 오류 발생."""
    seconds = max(1, min(seconds, 60))
    logger.info("dummy.sleep started", extra={"task_id": self.request.id, "seconds": seconds})

    if fail_prob > 0 and random.random() < fail_prob:
        raise TransientError(f"Simulated transient error (prob={fail_prob})")

    time.sleep(seconds)
    return {"slept": seconds}
