# 부하 테스트 시나리오 — 실시간 작업 큐 대시보드

- 최종 갱신: 2026-05-19 by 카맥
- 상위: [수진 PoC](../analysis/research-realtime-stack.md#4-실시간-옵션-poc-권장-시나리오-sse-검증), [T6](../tasks/T6-perf-carmack.md)
- 환경: Docker Compose 단일 머신. 스크립트 위치: `load_tests/`.

---

## 1. 사전 준비

```bash
# 의존성 설치
pip install locust==2.x redis requests

# 테스트 사용자 및 데이터 시드 (마크 구현 후 별도 픽스처 스크립트로 분리 예정)
python load_tests/seed.py --users 10 --jobs 10000

# 서비스 기동 (워커 수는 시나리오마다 달라짐)
docker compose up -d --scale worker=4 --scale api=1
```

---

## 2. 시나리오 매트릭스

> 총 3개 축의 조합. `M × N × K = 4 × 4 × 3 = 48` 조합 중 **중요 조합 16종**을 우선 실행.

| 축 | 값 |
|---|---|
| SSE 동시 연결 수 | 100 / 500 / 1000 / 2000 |
| Celery worker 수 | 2 / 4 / 8 / 16 |
| 작업 제출 RPS | 5 / 25 / 100 |

### 2.1 우선 실행 16종 (회귀 핵심)

| # | SSE 연결 | Worker 수 | 제출 RPS | 목적 |
|---|---|---|---|---|
| M-01 | 100 | 4 | 5 | 기본 베이스라인 |
| M-02 | 1000 | 4 | 5 | **SSE 1k 안정성** (budget P-04) |
| M-03 | 1000 | 4 | 25 | SSE 1k + 중간 부하 |
| M-04 | 1000 | 4 | 100 | SSE 1k + 고부하 |
| M-05 | 500 | 2 | 5 | 최소 구성 확인 |
| M-06 | 500 | 8 | 25 | 워커 스케일 효과 확인 |
| M-07 | 500 | 16 | 100 | 최대 워커 처리량 |
| M-08 | 2000 | 4 | 5 | SSE 2k 극단 테스트 |
| M-09 | 2000 | 8 | 25 | SSE 2k + 중간 부하 |
| M-10 | 100 | 2 | 100 | 워커 부족 시 큐 적체 확인 |
| M-11 | 100 | 4 | 100 | API 고부하 p95 확인 (budget P-01) |
| M-12 | 1000 | 8 | 25 | 스케일아웃 기준점 |
| M-13 | 1000 | 16 | 100 | 최대 구성 안정성 |
| M-14 | 2000 | 16 | 100 | 극단 조합 — 한계 탐색 |
| M-15 | 100 | 4 | 25 | 일반 운영 시뮬레이션 |
| M-16 | 500 | 4 | 25 | 일반 운영 + 중간 SSE |

---

## 3. Locust 스크립트

### 3.1 공통 설정 (`load_tests/config.py`)

```python
# load_tests/config.py — 부하 테스트 공통 설정
import os

BASE_URL = os.getenv("TARGET_URL", "http://localhost:5000")

# 테스트 계정 (seed.py로 사전 생성)
TEST_USERS = [
    {"email": f"perf_user_{i}@test.local", "password": "Perf@Test1234!"}
    for i in range(1, 51)  # 50개 계정 분산
]

# 타임아웃 (ms)
SSE_FIRST_EVENT_TIMEOUT_MS = 2000
API_REQUEST_TIMEOUT_S = 5
```

### 3.2 API 베이스라인 (`load_tests/locustfile_api.py`)

```python
# load_tests/locustfile_api.py — API 엔드포인트 p95 측정
import json, random, time
from locust import HttpUser, task, between, events
from config import TEST_USERS, API_REQUEST_TIMEOUT_S

class APIUser(HttpUser):
    wait_time = between(0.1, 0.5)
    token = None
    csrf_token = None

    def on_start(self):
        user = random.choice(TEST_USERS)
        resp = self.client.post("/auth/login", json=user, timeout=API_REQUEST_TIMEOUT_S)
        if resp.status_code == 204:
            me = self.client.get("/api/me", timeout=API_REQUEST_TIMEOUT_S)
            self.csrf_token = me.json().get("csrfToken")

    @task(3)
    def list_jobs(self):
        self.client.get("/api/jobs?limit=50", timeout=API_REQUEST_TIMEOUT_S)

    @task(2)
    def list_jobs_cursor(self):
        # 두 번째 페이지 cursor 시뮬레이션
        resp = self.client.get("/api/jobs?limit=50", timeout=API_REQUEST_TIMEOUT_S)
        if resp.status_code == 200:
            cursor = resp.json().get("nextCursor")
            if cursor:
                self.client.get(
                    f"/api/jobs?limit=50&cursor={cursor}",
                    timeout=API_REQUEST_TIMEOUT_S,
                    name="/api/jobs?cursor=[cursor]"
                )

    @task(2)
    def submit_job(self):
        import uuid
        self.client.post(
            "/api/jobs",
            json={"type": "dummy.sleep", "payload": {"seconds": 5}},
            headers={
                "X-CSRF-Token": self.csrf_token,
                "Idempotency-Key": str(uuid.uuid4()),
            },
            timeout=API_REQUEST_TIMEOUT_S,
        )

    @task(1)
    def get_job_detail(self):
        # 목록에서 임의 job_id 획득 후 상세 조회
        resp = self.client.get("/api/jobs?limit=10", timeout=API_REQUEST_TIMEOUT_S)
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
```

### 3.3 SSE 지연 측정 (`load_tests/locustfile_sse_latency.py`)

```python
# load_tests/locustfile_sse_latency.py — SSE 첫 이벤트 지연 및 push-to-receive 지연 측정
import time, json, random
from locust import HttpUser, task, events
from config import TEST_USERS, SSE_FIRST_EVENT_TIMEOUT_MS

class SSELatencyUser(HttpUser):
    """SSE 연결 후 첫 이벤트 도달 지연 측정 (budget P-02, P-03)."""

    def on_start(self):
        user = random.choice(TEST_USERS)
        self.client.post("/auth/login", json=user)

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
                                        import datetime
                                        emit_dt = datetime.datetime.fromisoformat(emit_at)
                                        recv_dt = datetime.datetime.now(datetime.timezone.utc)
                                        push_to_receive_ms = (recv_dt - emit_dt).total_seconds() * 1000
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
```

### 3.4 SSE 1k 동시 연결 (`load_tests/locustfile_sse_1k.py`)

```python
# load_tests/locustfile_sse_1k.py — 1k 동시 SSE 연결 안정성 (budget P-04)
import time, random, threading
from locust import HttpUser, task, events as locust_events
from config import TEST_USERS

HOLD_SECONDS = 300  # 5분 유지

class SSEConnectionUser(HttpUser):
    """연결 유지 5분 — 에러율 0% + 메모리 < 2GB 검증."""

    def on_start(self):
        user = random.choice(TEST_USERS)
        self.client.post("/auth/login", json=user)
        self._active = True

    def on_stop(self):
        self._active = False

    @task
    def hold_sse_connection(self):
        start = time.monotonic()
        received_chunks = 0

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
                    if chunk:
                        received_chunks += 1
                    if time.monotonic() > deadline or not self._active:
                        break
                elapsed_ms = (time.monotonic() - start) * 1000
                if elapsed_ms >= HOLD_SECONDS * 1000 * 0.95:  # 95% 이상 유지
                    resp.success()
                else:
                    resp.failure(f"연결이 {elapsed_ms:.0f}ms 만에 끊김 (목표 {HOLD_SECONDS*1000}ms)")
            except Exception as e:
                resp.failure(str(e))
```

### 3.5 워밍업 (`load_tests/locustfile_warmup.py`)

```python
# load_tests/locustfile_warmup.py — 서비스 워밍업 (캐시·연결 풀 초기화)
import random
from locust import HttpUser, task, between
from config import TEST_USERS

class WarmupUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        user = random.choice(TEST_USERS)
        self.client.post("/auth/login", json=user)

    @task(5)
    def list_jobs(self):
        self.client.get("/api/jobs?limit=50")

    @task(2)
    def get_me(self):
        self.client.get("/api/me")

    @task(1)
    def healthz(self):
        self.client.get("/healthz")
```

### 3.6 sampler 리더 락 승계 (`load_tests/test_leader_failover.py`)

```python
# load_tests/test_leader_failover.py — sampler 단일 리더 락 승계 시간 측정 (budget P-06)
"""
사용법:
  python test_leader_failover.py --api-count 2 --metrics-urls http://api1:5000/metrics http://api2:5000/metrics

동작:
  1. 현재 리더 인스턴스 식별 (queue_emitter_leader == 1)
  2. 리더 인스턴스 강제 종료 (docker kill)
  3. 비-리더 인스턴스의 queue_emitter_leader가 1이 될 때까지 시간 측정
  4. 승계 시간 < 5s 검증
"""
import argparse, time, subprocess, sys
import requests

def get_leader(metrics_urls: list[str]) -> str | None:
    for url in metrics_urls:
        try:
            text = requests.get(url, timeout=2).text
            for line in text.splitlines():
                if line.startswith("queue_emitter_leader") and not line.startswith("#"):
                    _, value = line.rsplit(" ", 1)
                    if float(value) == 1.0:
                        return url
        except Exception:
            continue
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-urls", nargs="+", required=True)
    parser.add_argument("--leader-container", required=True, help="리더 컨테이너 이름")
    parser.add_argument("--threshold-seconds", type=float, default=5.0)
    args = parser.parse_args()

    print("[P-06] 현재 리더 확인 중...")
    leader_url = get_leader(args.metrics_urls)
    if not leader_url:
        print("[P-06] 리더를 찾을 수 없음 — 서비스 상태 확인 필요.")
        sys.exit(1)
    print(f"[P-06] 리더: {leader_url}")

    print(f"[P-06] 리더 컨테이너 강제 종료: {args.leader_container}")
    subprocess.run(["docker", "kill", args.leader_container], check=True)
    kill_time = time.monotonic()

    print("[P-06] 승계 대기 중...")
    while True:
        new_leader = get_leader([u for u in args.metrics_urls if u != leader_url])
        if new_leader:
            elapsed = time.monotonic() - kill_time
            print(f"[P-06] 승계 완료: {elapsed:.2f}s (임계값 {args.threshold_seconds}s)")
            if elapsed <= args.threshold_seconds:
                print("[P-06] PASS")
                sys.exit(0)
            else:
                print("[P-06] FAIL — 임계값 초과")
                sys.exit(1)
        if time.monotonic() - kill_time > args.threshold_seconds * 3:
            print("[P-06] FAIL — 타임아웃 (리더 미확인)")
            sys.exit(1)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
```

### 3.7 budget 검증 헬퍼 (`load_tests/check_budget.py`)

```python
# load_tests/check_budget.py — CI에서 Prometheus 메트릭 기반 budget 검증
"""
사용법:
  python check_budget.py --scenario P-01 --threshold-p95 200 --metrics-url http://localhost:5000/metrics
"""
import argparse, sys
import requests

QUANTILE_LABELS = {
    "P-01": ("http_request_duration_seconds", {"quantile": "0.95"}),
    "P-02": ("sse_emit_to_receive_seconds", {"quantile": "0.95", "channel": "user", "client_type": "test"}),
    "P-03": ("sse_emit_to_receive_seconds", {"quantile": "0.95", "channel": "job", "client_type": "test"}),
    "P-07": ("http_request_duration_seconds", {"quantile": "0.95", "route": "/api/jobs"}),
}

def get_metric_value(metrics_text: str, metric_name: str, labels: dict) -> float | None:
    for line in metrics_text.splitlines():
        if line.startswith("#"):
            continue
        if not line.startswith(metric_name):
            continue
        label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
        if label_str in line:
            try:
                return float(line.split()[-1]) * 1000  # seconds → ms
            except ValueError:
                continue
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--threshold-p95", type=float, required=True)
    parser.add_argument("--metrics-url", default="http://localhost:5000/metrics")
    args = parser.parse_args()

    text = requests.get(args.metrics_url, timeout=5).text
    metric_name, labels = QUANTILE_LABELS.get(args.scenario, (None, {}))
    if not metric_name:
        print(f"[budget] 알 수 없는 시나리오: {args.scenario}")
        sys.exit(1)

    value = get_metric_value(text, metric_name, labels)
    if value is None:
        print(f"[budget] 메트릭 {metric_name} 값을 찾을 수 없음.")
        sys.exit(1)

    print(f"[budget] {args.scenario}: p95 = {value:.1f}ms (임계값 {args.threshold_p95}ms)")
    if value <= args.threshold_p95:
        print("[budget] PASS")
        sys.exit(0)
    else:
        print(f"[budget] FAIL — {value:.1f}ms > {args.threshold_p95}ms")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 4. 매트릭스 실행 자동화 (`load_tests/run_matrix.sh`)

```bash
#!/usr/bin/env bash
# load_tests/run_matrix.sh — T6 시나리오 매트릭스 실행
# 사용법: ./run_matrix.sh [--quick] 빠른 검증 시 --quick 플래그

set -euo pipefail

RESULTS_DIR="results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# 기본값
HOLD_TIME=300
RUN_TIME=120

if [[ "${1:-}" == "--quick" ]]; then
  HOLD_TIME=60
  RUN_TIME=30
fi

run_scenario() {
  local id="$1" sse_users="$2" workers="$3" rps="$4"
  echo "=== $id: SSE=$sse_users, workers=$workers, rps=$rps ==="

  docker compose up -d --scale worker="$workers" --no-recreate

  locust -f load_tests/locustfile_sse_1k.py \
    --headless -u "$sse_users" -r $(( sse_users / 20 )) \
    --host http://localhost:5000 \
    --run-time "${RUN_TIME}s" \
    --csv "$RESULTS_DIR/${id}" \
    --html "$RESULTS_DIR/${id}_report.html" \
    2>&1 | tail -5

  docker stats --no-stream --format "{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}" \
    >> "$RESULTS_DIR/${id}_stats.txt"

  echo "--- $id 완료 ---"
}

# 우선 실행 16종
run_scenario M-01 100  4  5
run_scenario M-02 1000 4  5
run_scenario M-03 1000 4  25
run_scenario M-04 1000 4  100
run_scenario M-05 500  2  5
run_scenario M-06 500  8  25
run_scenario M-07 500  16 100
run_scenario M-08 2000 4  5
run_scenario M-09 2000 8  25
run_scenario M-10 100  2  100
run_scenario M-11 100  4  100
run_scenario M-12 1000 8  25
run_scenario M-13 1000 16 100
run_scenario M-14 2000 16 100
run_scenario M-15 100  4  25
run_scenario M-16 500  4  25

echo "=== 매트릭스 완료. 결과: $RESULTS_DIR ==="
```

---

## 5. 측정 결과 요약 테이블 (실행 후 기입)

| # | SSE 연결 | Worker | RPS | p95 API | SSE 에러율 | 메모리 | throughput | 결과 |
|---|---|---|---|---|---|---|---|---|
| M-01 | 100 | 4 | 5 | TBD | TBD | TBD | TBD | ⬜ |
| M-02 | 1000 | 4 | 5 | TBD | TBD | TBD | TBD | ⬜ |
| M-03 | 1000 | 4 | 25 | TBD | TBD | TBD | TBD | ⬜ |
| M-04 | 1000 | 4 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-05 | 500 | 2 | 5 | TBD | TBD | TBD | TBD | ⬜ |
| M-06 | 500 | 8 | 25 | TBD | TBD | TBD | TBD | ⬜ |
| M-07 | 500 | 16 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-08 | 2000 | 4 | 5 | TBD | TBD | TBD | TBD | ⬜ |
| M-09 | 2000 | 8 | 25 | TBD | TBD | TBD | TBD | ⬜ |
| M-10 | 100 | 2 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-11 | 100 | 4 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-12 | 1000 | 8 | 25 | TBD | TBD | TBD | TBD | ⬜ |
| M-13 | 1000 | 16 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-14 | 2000 | 16 | 100 | TBD | TBD | TBD | TBD | ⬜ |
| M-15 | 100 | 4 | 25 | TBD | TBD | TBD | TBD | ⬜ |
| M-16 | 500 | 4 | 25 | TBD | TBD | TBD | TBD | ⬜ |

결과 컬럼 범례: ✅ PASS / ❌ FAIL(budget 초과) / ⬜ 미실행

---

## 6. 수진 PoC 흡수 내역

수진([research-realtime-stack.md §4](../analysis/research-realtime-stack.md#4-실시간-옵션-poc-권장-시나리오-sse-검증))의 최소 PoC 스크립트를 확장.

| PoC 항목 | T6 흡수 위치 | 확장 내용 |
|---|---|---|
| `sse_poc.py` Flask 서버 | T4 마크 구현으로 대체 | 인증·CSRF·데이터모델 포함 완전 구현 |
| `locustfile.py` 기본 측정 | `locustfile_sse_latency.py` §3.3 | push-to-receive `_emit_at` 측정 추가 |
| 1k 연결 Locust 명령 | `locustfile_sse_1k.py` §3.4 | 5분 유지·에러율·메모리 측정 포함 |
| 4가지 측정 항목 표 | `baseline.md §4` | N=10 반복·SD 포함으로 강화 |
