# SSE 첫 이벤트 지연 및 push-to-receive 지연 측정 — budget P-02 (SSE p95 < 500ms)
import time
import json
import random
from locust import HttpUser, task, events
from config import TEST_USERS, SSE_FIRST_EVENT_TIMEOUT_MS


class SSELatencyUser(HttpUser):
    """SSE 연결 후 첫 이벤트 도달 지연 측정 (budget P-02)."""

    csrf_token = None

    def on_start(self):
        user = random.choice(TEST_USERS)
        resp = self.client.post("/api/auth/login", json=user)
        if resp.status_code == 200:
            self.csrf_token = resp.json().get("csrf_token")

    @task
    def measure_first_event_latency(self):
        start_ms = time.monotonic() * 1000
        first_event_ms = None

        with self.client.get(
            "/api/events/jobs",
            stream=True,
            catch_response=True,
            timeout=SSE_FIRST_EVENT_TIMEOUT_MS / 1000,
            name="/api/events/jobs [SSE first-event]",
            headers={"X-Perf-Client": "test"},
        ) as resp:
            try:
                for chunk in resp.iter_content(chunk_size=None):
                    if chunk and chunk.strip():
                        first_event_ms = (time.monotonic() * 1000) - start_ms
                        # push-to-receive: _emit_at 파싱
                        try:
                            lines = chunk.decode().strip().split("\n")
                            for line in lines:
                                if line.startswith("data:"):
                                    data = json.loads(line[5:].strip())
                                    emit_at = data.get("_emit_at")
                                    if emit_at:
                                        push_to_receive_ms = (time.time() - float(emit_at)) * 1000
                                        events.request.fire(
                                            request_type="SSE",
                                            name="/api/events/jobs [push-to-receive]",
                                            response_time=push_to_receive_ms,
                                            response_length=len(chunk),
                                            exception=None,
                                            context={},
                                        )
                        except Exception:
                            pass
                        resp.success()
                        break
            except Exception as e:
                resp.failure(str(e))
                return

        if first_event_ms is not None:
            events.request.fire(
                request_type="SSE",
                name="/api/events/jobs [first-event-latency]",
                response_time=first_event_ms,
                response_length=0,
                exception=None,
                context={},
            )
