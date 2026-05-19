# 성능 회귀 시나리오 및 Perf Budget — 실시간 작업 큐 대시보드

- 최종 갱신: 2026-05-19 by 카맥 (제임스 사인오프 반영)
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [T6](../tasks/T6-perf-carmack.md)
- 권위: 본 문서가 T6 스코프 내 "성능 평가 4축 중 성능 축"의 SSOT.

---

## 1. Perf Budget 표

> budget 초과 PR은 **카맥이 머지 차단**. 위반 발견 시 마크에게 Jira Sub-task 자동 생성.

| 지표 | Budget | 측정 방법 | 비고 |
|---|---|---|---|
| API p95 latency | **< 200ms** | Locust + `/metrics` `http_request_duration_seconds` histogram | 모든 엔드포인트 (단, `/healthz` 제외) |
| SSE 푸시 지연 p95 | **< 500ms** | `_emit_at` 부착 → 클라 수신 시각 차이 (`sse_emit_to_receive_seconds` 히스토그램) | 테스트 빌드 한정 메커니즘 |
| SSE 첫 이벤트 지연 p95 | **< 500ms** | Locust 연결 후 첫 chunk 도착 시각 | cold 연결 포함 |
| 1k 동시 SSE 연결 안정성 | 5분 유지, **에러율 0%**, 메모리 < 2GB | Locust `-u 1000 --run-time 300s` + `docker stats` | gunicorn gevent 4 workers |
| Celery throughput | **≥ 2 job/s/worker** (더미 5s 작업 기준) | `queue.workers.throughput` 메트릭 (`job_outcomes_total` 60s 윈도우 ÷ worker 수) | worker 4 기준 시스템 전체 ≥ 8 job/s |
| sampler 단일 리더 락 승계 | 락 만료 시 **5초 이내** 승계 | 리더 인스턴스 강제 종료 후 `queue_emitter_leader` gauge가 다른 인스턴스로 전환되는 시간 | `heartbeat:queue_emitter` EX=10s |
| `/healthz` p95 | **< 50ms** | Locust GET `/healthz` N=10 | LB 헬스체크 경로 |
| API 에러율 | **< 0.1%** (정상 부하) | `http_requests_total{status=~"5.."}` / 전체 | 503·502 제외 (인프라 재시작 시) |

---

## 2. 성능 회귀 시나리오 목록

| # | 시나리오 이름 | 스크립트 | 임계값 | 자동화 상태 | 담당 |
|---|---|---|---|---|---|
| P-01 | API 응답 시간 회귀 | `load_tests/locustfile_api.py` | p95 < 200ms | ⬜ CI nightly 예정 | 카맥 |
| P-02 | SSE 첫 이벤트 지연 | `load_tests/locustfile_sse_latency.py` | p95 < 500ms | ⬜ CI nightly 예정 | 카맥 |
| P-03 | SSE push-to-receive 지연 | `load_tests/locustfile_sse_push.py` | p95 < 500ms | ⬜ 구현(T4) 완료 후 | 카맥+네이선 |
| P-04 | 1k 동시 SSE 연결 안정성 | `load_tests/locustfile_sse_1k.py` | 에러율 0%, 메모리 < 2GB | ⬜ 주간 nightly | 카맥 |
| P-05 | Celery throughput | Prometheus `queue.workers.throughput` 모니터링 | ≥ 2 job/s/worker | ⬜ 상시 메트릭 감시 | 카맥 |
| P-06 | sampler 리더 락 승계 | `load_tests/test_leader_failover.py` | 5초 이내 | ⬜ 구현(T4) 완료 후 | 카맥 |
| P-07 | DB 쿼리 회귀 (jobs 목록) | Prometheus `http_request_duration_seconds{route="/api/jobs"}` | p95 < 200ms | ⬜ CI nightly 예정 | 카맥 |
| P-08 | 메모리 누수 (장기 운전) | `load_tests/locustfile_sse_1k.py` 30분 연장 | RSS 선형 증가 없음 | ⬜ 주간 | 카맥 |

---

## 3. 위반 대응 절차

### 3.1 PR 단계 (per-PR 게이트)

```
마크가 PR 오픈
  → CI가 P-01 (API p95), P-02 (SSE 첫 이벤트 지연) 자동 실행
  → budget 초과 시: 카맥 → 마크 team-send "[Perf 회귀] PR #NNN..."
  → 마크가 수정 후 재실행
  → 통과 시 카맥 머지 승인 코멘트
```

### 3.2 nightly 자동화 단계

```
카맥 nightly 스크립트 실행
  → P-01~P-05 전체 시나리오 순차 실행
  → 임계값 초과 항목 발견 시:
      team-send 마크 "[Perf 회귀] P-0N 임계 초과 — baseline 대비 XX% 악화. Jira 자동 생성."
      Jira Sub-task 자동 생성 (상위: 해당 스프린트 Epic)
  → 시스템 레벨 결정 필요 시:
      team-send 네이선 "[Perf 에스컬레이션] ..."
      team-send 제임스 "[Perf 에스컬레이션] ..."
```

### 3.3 임계값 조정 절차

- budget 표(본 문서 §1) 변경은 **제임스 승인 필수**.
- 조정 제안은 `team-send 제임스` 로 데이터 근거와 함께 제출.
- 승인 후 본 문서 §1·§2 동시 갱신 + PR 게이트 스크립트 반영.

---

## 4. 메트릭 연결 (ADR-001 §7.2 카탈로그)

| Prometheus 메트릭 | 타입 | 연결 Budget 항목 |
|---|---|---|
| `http_request_duration_seconds` | histogram | P-01, P-07 |
| `http_requests_total` | counter | API 에러율 |
| `job_queue_length` | gauge | 대기열 압박 감시 |
| `job_duration_seconds` | histogram | P-05 throughput 추론 |
| `job_outcomes_total` | counter | P-05 throughput 산출 (`succeeded+failed / 60s`) |
| `sse_clients_active` | gauge | P-04 연결 수 감시 |
| `sse_messages_sent_total` | counter | SSE 처리량 추세 |
| `queue_emitter_leader` | gauge | P-06 리더 승계 감시 |
| `sse_emit_to_receive_seconds` *(추가)* | histogram | P-03 push-to-receive 지연 |

> `sse_emit_to_receive_seconds` 는 ADR-001에 없는 추가 메트릭. T6 E항 네이선 협업 후 마크가 구현.

---

## 5. 회귀 방지 CI 통합 (예정)

```yaml
# .github/workflows/perf-gate.yml (예시 — T4 구현 후 마크와 협업)
name: Perf Gate
on:
  pull_request:
    branches: [develop/**, main]

jobs:
  perf-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker compose up -d --scale worker=4
      - name: Warmup
        run: locust -f load_tests/locustfile_warmup.py --headless -u 20 -r 5 --run-time 60s --host http://localhost:5000
      - name: API p95 check (P-01)
        run: python load_tests/check_budget.py --scenario P-01 --threshold-p95 200
      - name: SSE latency check (P-02)
        run: python load_tests/check_budget.py --scenario P-02 --threshold-p95 500
```

---

## 변경 이력

| 일자 | 변경 | 승인 |
|---|---|---|
| 2026-05-19 | 초안 작성 (T6 위임 수신) | 제임스 승인 대기 |
| 2026-05-19 | §1 Perf Budget 표 8항목 전면 발효. per-PR 게이트 P-01·P-02 가동 승인. | **제임스 사인오프** (inspection-T6-carmack.md) |
