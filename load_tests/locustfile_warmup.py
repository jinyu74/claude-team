# 서비스 워밍업 — 캐시·연결 풀 초기화용 부하 생성
import random
from locust import HttpUser, task, between
from config import TEST_USERS


class WarmupUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        user = random.choice(TEST_USERS)
        self.client.post("/api/auth/login", json=user)

    @task(5)
    def list_jobs(self):
        self.client.get("/api/jobs?limit=50")

    @task(2)
    def get_me(self):
        self.client.get("/api/me")

    @task(1)
    def healthz(self):
        self.client.get("/healthz")
