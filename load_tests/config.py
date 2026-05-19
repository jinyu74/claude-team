# 부하 테스트 공통 설정
import os

BASE_URL = os.getenv("TARGET_URL", "http://localhost:5000")

TEST_USERS = [
    {"email": f"perf_user_{i}@test.local", "password": "Perf@Test1234!"}
    for i in range(1, 51)
]

SSE_FIRST_EVENT_TIMEOUT_MS = 2000
API_REQUEST_TIMEOUT_S = 5
