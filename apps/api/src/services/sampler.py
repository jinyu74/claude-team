# 큐 상태 샘플러 — 단일 리더 락 + Prometheus 게이지 갱신
import time
import threading
import redis as redis_lib
from src.models.job import Job, JOB_STATUSES
from src.utils.metrics import job_queue_length, queue_emitter_leader

LEADER_KEY = "heartbeat:queue_emitter"
LEADER_TTL = 10  # 초
SAMPLE_INTERVAL = 5  # 초


def _try_acquire_leader(r: redis_lib.Redis) -> bool:
    return bool(r.set(LEADER_KEY, "1", ex=LEADER_TTL, nx=True))


def _renew_leader(r: redis_lib.Redis) -> bool:
    return bool(r.expire(LEADER_KEY, LEADER_TTL))


def _sample(app, r: redis_lib.Redis) -> None:
    with app.app_context():
        for status in JOB_STATUSES:
            count = Job.query.filter_by(status=status).count()
            job_queue_length.labels(status=status).set(count)


def run_sampler_loop(app, r: redis_lib.Redis) -> None:
    """백그라운드 스레드에서 실행. 단일 리더만 샘플링을 수행한다."""
    is_leader = False
    while True:
        if is_leader:
            if _renew_leader(r):
                queue_emitter_leader.set(1)
                _sample(app, r)
            else:
                is_leader = False
                queue_emitter_leader.set(0)
        else:
            if _try_acquire_leader(r):
                is_leader = True
                queue_emitter_leader.set(1)
                _sample(app, r)
            else:
                queue_emitter_leader.set(0)
        time.sleep(SAMPLE_INTERVAL)


def start_sampler(app, r: redis_lib.Redis) -> None:
    t = threading.Thread(target=run_sampler_loop, args=(app, r), daemon=True)
    t.start()
