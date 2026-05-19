# Celery 앱 설정 — Flask 앱 컨텍스트 연동
from celery import Celery

from src.config import Config


def make_celery(app=None) -> Celery:
    broker = Config.REDIS_URL
    celery = Celery(
        "taskqueue",
        broker=broker,
        backend=broker,
        include=["src.worker.tasks"],
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "src.worker.tasks.dummy_sleep": {"queue": "default"},
        },
    )

    if app is not None:
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        celery.Task = ContextTask

    return celery


celery = make_celery()
