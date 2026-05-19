# Task T6 → 카맥 (Performance)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-29 EOD (베이스라인 + budget 표), 이후 상시 게이트
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [수진 PoC](../analysis/research-realtime-stack.md#4-실시간-옵션-poc-권장-시나리오-sse-검증)

## 목적

성능 베이스라인을 만들고 budget 게이트를 운영. **성능 축의 게이트키퍼**.

## 스코프

### A. 베이스라인 (`docs/performance/baseline.md`)

- 환경 명세 (CPU·RAM·Redis 버전 7.4.2·PG 16·gunicorn worker 수·Celery worker 수).
- API 엔드포인트 10종 p50/p95/p99 (warm/cold).
- SSE 첫 이벤트 지연 + push-to-receive 지연 p95.
- DB 쿼리 p95 (작업 제출·목록·상세·페이지네이션).
- N=10 반복, 분산(SD) 명시.

### B. Perf Budget 표 (`docs/performance/regression-perf.md`)

- 결정 메모의 평가 기준 4축 중 "성능" 의 권위 문서.

| 지표 | budget | 측정 방법 |
|---|---|---|
| API p95 | < 200ms | Locust + `/metrics` `http_request_duration_seconds` |
| SSE 푸시 지연 p95 | < 500ms | 워커가 publish 직전 timestamp 부착, 클라(테스트 클라이언트) 가 수신 시각과 차이 측정 |
| SSE 첫 이벤트 지연 p95 | < 500ms | Locust 첫 chunk 도착 시각 |
| 1k 동시 SSE 연결 | 5분 유지·에러율 0%·메모리 < 2GB | Locust `-u 1000` |
| Celery 작업 throughput | ≥ 2 job/s/worker (더미 5s) | `queue.workers.throughput` |
| sampler 단일 리더 락 | 락 만료 시 5초 내 승계 | 강제 종료 후 다른 인스턴스 takeover 측정 |

- budget 초과 PR 은 머지 차단. 회귀 시 마크에게 Jira 자동 생성.

### C. 부하 시나리오 (`docs/performance/load-tests.md`)

- 수진 PoC (Locust + Gunicorn gevent) 흡수·확장.
- 시나리오 매트릭스:
  - SSE 연결 수: 100 / 500 / 1000 / 2000
  - 워커 수: 2 / 4 / 8 / 16
  - 작업 제출 RPS: 5 / 25 / 100
- 회귀 환경 — Docker Compose 단일 머신, 결과는 베이스라인 갱신 트리거.

### D. 메트릭 대시보드 (`infra/grafana/dashboard.json` 권장)

- ADR §7.2 메트릭 카탈로그 + 본 T6 추가 메트릭.
- 패널: API latency·error rate, queue 길이·throughput·outcomes, SSE clients·messages·channel 별, `queue_emitter_leader` gauge.

### E. SSE 푸시 지연 측정 메커니즘 (네이선 협업)

- 워커가 `job_events.payload` 에 `_emit_at` (서버 monotonic + UTC) 부착.
- 테스트 클라이언트가 수신 시각 (`receive_at`) 과 차이 기록. 운영 사용자 메시지는 `_emit_at` 노출 금지(테스트 빌드 한정).
- 운영용은 `sse_emit_to_receive_seconds` 히스토그램 (테스트 클라이언트 한정 라벨).

## 산출물

- `docs/performance/baseline.md`, `docs/performance/regression-perf.md`, `docs/performance/load-tests.md`, `infra/grafana/dashboard.json`.

## 완료 조건

- 베이스라인 N=10 측정 완료.
- budget 표 합의(제임스 승인) 후 PR 게이트 가동.
- Locust 시나리오 매트릭스 실행 가능 상태.

## 회신 방법

베이스라인·budget 초안 완료 시 `team-send 제임스 "[결과] T6 베이스라인·budget 초안 완료"` 회신. 마크 PR 의 perf 게이트는 카맥 → 마크 직접 송신.
