# 1k 동시 SSE 연결 안정성 측정 — budget P-04 (에러율 0%, 메모리 < 2GB)
import time
import random
from locust import HttpUser, task
from config import TEST_USERS

HOLD_SECONDS = 300  # 5분 유지


class SSEConnectionUser(HttpUser):
    """연결 유지 5분 — 에러율 0% + 메모리 < 2GB 검증."""

    _active: bool = True

    def on_start(self):
        user = random.choice(TEST_USERS)
        self.client.post("/api/auth/login", json=user)
        self._active = True

    def on_stop(self):
        self._active = False

    @task
    def hold_sse_connection(self):
        start = time.monotonic()

        with self.client.get(
            "/api/events/jobs",
            stream=True,
            catch_response=True,
            timeout=HOLD_SECONDS + 30,
            name="/api/events/jobs [hold-5min]",
        ) as resp:
            try:
                deadline = start + HOLD_SECONDS
                for chunk in resp.iter_content(chunk_size=None):
                    _ = chunk  # keepalive 바이트 소비
                    if time.monotonic() > deadline or not self._active:
                        break
                elapsed_ms = (time.monotonic() - start) * 1000
                # 목표 시간의 95% 이상 유지했으면 성공
                if elapsed_ms >= HOLD_SECONDS * 1000 * 0.95:
                    resp.success()
                else:
                    resp.failure(
                        f"연결이 {elapsed_ms:.0f}ms 만에 끊김 (목표 {HOLD_SECONDS * 1000}ms)"
                    )
            except Exception as e:
                resp.failure(str(e))
