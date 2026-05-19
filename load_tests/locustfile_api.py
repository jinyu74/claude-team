# API 엔드포인트 p95 측정 — budget P-01 (API p95 < 200ms)
import json
import random
import uuid
from locust import HttpUser, task, between
from config import TEST_USERS, API_REQUEST_TIMEOUT_S


class APIUser(HttpUser):
    wait_time = between(0.1, 0.5)
    csrf_token = None

    def on_start(self):
        user = random.choice(TEST_USERS)
        resp = self.client.post("/api/auth/login", json=user, timeout=API_REQUEST_TIMEOUT_S)
        if resp.status_code == 200:
            self.csrf_token = resp.json().get("csrf_token")

    @task(3)
    def list_jobs(self):
        self.client.get(
            "/api/jobs?limit=50",
            headers={"X-CSRF-Token": self.csrf_token},
            timeout=API_REQUEST_TIMEOUT_S,
        )

    @task(2)
    def list_jobs_with_status(self):
        status = random.choice(["pending", "running", "succeeded", "failed"])
        self.client.get(
            f"/api/jobs?status={status}&limit=50",
            headers={"X-CSRF-Token": self.csrf_token},
            timeout=API_REQUEST_TIMEOUT_S,
            name="/api/jobs?status=[status]",
        )

    @task(2)
    def submit_job(self):
        if not self.csrf_token:
            return
        self.client.post(
            "/api/jobs",
            json={"type": "dummy.sleep", "payload": {"seconds": 5, "fail_prob": 0.0}, "priority": 0},
            headers={
                "X-CSRF-Token": self.csrf_token,
                "Idempotency-Key": str(uuid.uuid4()),
            },
            timeout=API_REQUEST_TIMEOUT_S,
        )

    @task(1)
    def get_job_detail(self):
        resp = self.client.get(
            "/api/jobs?limit=10",
            headers={"X-CSRF-Token": self.csrf_token},
            timeout=API_REQUEST_TIMEOUT_S,
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            if items:
                job_id = random.choice(items)["id"]
                self.client.get(
                    f"/api/jobs/{job_id}",
                    name="/api/jobs/[id]",
                    timeout=API_REQUEST_TIMEOUT_S,
                )

    @task(1)
    def healthz(self):
        self.client.get("/healthz", timeout=API_REQUEST_TIMEOUT_S)
