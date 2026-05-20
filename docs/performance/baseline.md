# 성능 베이스라인 — 실시간 작업 큐 대시보드

- 최종 갱신: 2026-05-20 by 카맥
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [T6](../tasks/T6-perf-carmack.md)
- 상태: **부분 확정** (§3.1 API warm N=10 실측 완료 — budget 초과 3항목 발견 / §3.2 cold·§4 SSE·§5 DB·§6 Celery 는 PR #11 머지 후 진행 예정)

---

## 1. 환경 명세

> 아래 표는 **측정 기준 환경**. 모든 베이스라인 측정은 이 환경 또는 동일 스펙에서만 유효.

| 항목 | 값 |
|---|---|
| 측정 머신 | Docker Compose 단일 머신 (macOS 개발 환경) |
| CPU | Apple M3 · 8 vCPU (performance 4 + efficiency 4) |
| RAM | 24 GB unified memory |
| OS | Darwin 25.0.0 arm64 (macOS Sequoia) |
| Redis 버전 | **7.4.2** (CVE-2025-49844 픽스 포함 — R-006) |
| PostgreSQL 버전 | **16.x** |
| gunicorn worker 수 | **4** (gevent, `--worker-connections 1000`) |
| Celery worker 수 | **4** (default 큐, `acks_late=True`) |
| 측정 도구 | Locust 2.x, `psutil`, `docker stats`, `/metrics` Prometheus 스크래핑 |
| 데이터 상태 | warm (Redis 캐시·세션 사전 준비 완료, PG 10k jobs 시드) |
| N | **10** (단발 측정 금지 — §2 참조) |
| api 호스트 포트 | **5001** (macOS Control Center / AirPlay Receiver가 5000 점유 — PR #9 우회) |

---

## 2. 측정 방법론

1. 각 시나리오는 **N=10 반복** 실행. 분산(SD)·min·max 함께 기록.
2. warm 측정 전 1분 워밍업 실행 후 측정 시작.
3. cold 측정은 Redis flush + gunicorn 재시작 후 첫 요청 기록.
4. 부하 발생기(Locust)와 측정 대상 서버는 **같은 Docker network** 내에서 실행 (네트워크 왕복 오버헤드 최소화).
5. 결과는 `/metrics` Prometheus 엔드포인트의 히스토그램 버킷에서 p50/p95/p99 산출 또는 Locust 통계 직접 수집.
6. 베이스라인 갱신 트리거: 메이저 릴리스·인프라 변경·perf budget 임계값 초과 확인 시.

---

## 3. API 엔드포인트 베이스라인

> p50/p95/p99 단위: ms. throughput 단위: req/s. N=10.

### 3.1 warm 베이스라인

> 측정일: 2026-05-20 / 환경: §1 Docker Compose (Apple M3, macOS 25.0.0) / N=10 / VU=50, ramp 10/s / run-time 30s × 10

| 엔드포인트 | 메서드 | p50 | p95 (±SD) | p99 | err% | throughput | budget | 상태 |
|---|---|---|---|---|---|---|---|---|
| `POST /api/auth/login` | POST | 332ms | 415ms (±57ms) | 444ms | 0% | 1.7 rps | p95 < 200ms | ⚠️ **초과** |
| `DELETE /auth/session` | DELETE | TBD | TBD | TBD | TBD | TBD | p95 < 200ms | 미측정 |
| `GET /api/me` | GET | TBD | TBD | TBD | TBD | TBD | p95 < 200ms | 미측정 |
| `POST /api/jobs` | POST | 20ms | 224ms (±91ms) | 605ms | 0% | 31.0 rps | p95 < 200ms | ⚠️ **초과** |
| `GET /api/jobs` (cursor, limit 50) | GET | 8ms | 99ms (±49ms) | 430ms | 0% | 45.7 rps | p95 < 200ms | ✅ |
| `GET /api/jobs` (첫 페이지, limit 10) | GET | 8ms | 109ms (±59ms) | 414ms | 0% | 15.3 rps | p95 < 200ms | ✅ |
| `GET /api/jobs/:id` | GET | 6ms | 88ms (±50ms) | 214ms | 0% | 15.2 rps | p95 < 200ms | ✅ |
| `GET /api/jobs?status=[status]` | GET | 7ms | 97ms (±46ms) | 379ms | 0% | 30.8 rps | p95 < 200ms | ✅ |
| `PATCH /api/jobs/:id` (cancel) | PATCH | TBD | TBD | TBD | TBD | TBD | p95 < 200ms | 미측정 |
| `PATCH /api/jobs/:id` (retry) | PATCH | TBD | TBD | TBD | TBD | TBD | p95 < 200ms | 미측정 |
| `GET /healthz` | GET | 6ms | 105ms (±50ms) | 320ms | 0% | 15.5 rps | p95 < 50ms | ⚠️ **초과** |

**budget 초과 분석:**
- `POST /api/auth/login` — argon2id 해싱 비용. work factor 조정 또는 budget 재검토 필요. → 마크 위임.
- `POST /api/jobs` — p95 224ms (±91ms), SD 큼. DB INSERT + Redis ENQUEUE 경로 지연 스파이크. §5 DB 쿼리 실측 후 병목 특정.
- `GET /healthz` — p95 105ms, budget 50ms. gunicorn 내부 오버헤드 또는 DB ping 포함 여부 확인 필요.

### 3.2 cold 베이스라인 (Redis flush + gunicorn 재시작 후 첫 요청)

| 엔드포인트 | p95 cold | p95 warm | 차이 | 메모 |
|---|---|---|---|---|
| `GET /api/me` | TBD | TBD | TBD | 세션 캐시 미스 영향 측정 |
| `GET /api/jobs` | TBD | TBD | TBD | PG 쿼리 플랜 캐시 영향 |
| `POST /api/jobs` | TBD | TBD | TBD | Redis 연결 풀 초기화 포함 |

---

## 4. SSE 베이스라인

| 지표 | 측정 방법 | p50 | p95 (±SD) | budget |
|---|---|---|---|---|
| 첫 이벤트 지연 | Locust — 연결 후 첫 chunk 도착까지 | TBD | TBD | < 500ms |
| push-to-receive 지연 | `_emit_at` 부착 → 클라 수신 시각 차이 | TBD | TBD | < 500ms |
| 1k 동시 연결 안정성 | Locust `-u 1000` 5분 — 에러율 | TBD | TBD | 에러 0% |
| 1k 연결 메모리 | `docker stats` — gunicorn RSS | TBD | TBD | < 2GB |
| keep-alive 주석 수신 | `: ping\n\n` 15s 간격 확인 | TBD | TBD | 15s ±2s |

### 4.1 push-to-receive 지연 측정 메커니즘

워커가 Redis에 publish 직전 `job_events.payload._emit_at` (UTC ISO-8601 + monotonic_ns) 부착.
테스트 클라이언트가 SSE 메시지 수신 시각 `receive_at` 을 기록 후 차이 계산.

```
push_to_receive_ms = (receive_at - _emit_at) × 1000
```

- **테스트 빌드 전용** — 운영 사용자 응답에 `_emit_at` 노출 금지.
- **`X-Perf-Client: test` 헤더 필수** — 헤더 미존재 시 API가 `_emit_at` strip 처리. 측정 불가 (ADR-001 §5.4.3).
- Prometheus 히스토그램: `sse_emit_to_receive_seconds{channel="user"|"job", client_type="test"}` (테스트 클라이언트 라벨 한정).

---

## 5. DB 쿼리 베이스라인

> Prometheus `http_request_duration_seconds` 에서 주요 쿼리 경로 분리 측정 또는 SQLAlchemy 이벤트 훅.

| 쿼리 | 시나리오 | p95 (±SD) | budget |
|---|---|---|---|
| `jobs INSERT` (작업 제출) | jobs 10k 시드 상태 | TBD | < 30ms |
| `jobs SELECT` (목록, limit 50) | idx_jobs_user_created 활용 | TBD | < 20ms |
| `jobs SELECT` (상세 + recentEvents) | idx_job_events_job_created 활용 | TBD | < 30ms |
| `jobs SELECT` (페이지네이션 cursor) | created_at DESC cursor | TBD | < 20ms |
| `job_events INSERT` (이벤트 기록) | 동시 워커 4 상황 | TBD | < 10ms |

---

## 6. Celery 워커 베이스라인

| 지표 | 측정 조건 | 값 | budget |
|---|---|---|---|
| throughput (job/s/worker) | 더미 5s 작업, 워커 4 | TBD | ≥ 2 job/s/worker |
| sampler 리더 락 승계 시간 | 리더 인스턴스 강제 종료 후 | TBD | < 5s |
| `queue.counts` 발행 주기 지터 | 1s 주기, N=10 간격 측정 | TBD | < ±200ms |
| `queue.workers` 발행 주기 지터 | 5s 주기, N=10 간격 측정 | TBD | < ±500ms |

---

## 7. 베이스라인 측정 명령 모음

```bash
# 1. 환경 정보 수집
lscpu | grep -E "CPU|Thread|Core|Socket"
free -h
docker --version && docker compose version

# 2. 서비스 시작 (단일 머신 Docker Compose)
docker compose up -d --scale worker=4 --scale api=1

# 3. warm-up (1분)
locust -f load_tests/locustfile_warmup.py --headless -u 20 -r 5 \
  --host http://localhost:5001 --run-time 60s

# 4. API 베이스라인 측정 (N=10 반복, warm)
for i in $(seq 1 10); do
  locust -f load_tests/locustfile_api.py --headless -u 50 -r 10 \
    --host http://localhost:5001 --run-time 30s \
    --csv "results/api_warm_run${i}" --csv-full-history
done

# 5. SSE 동시 연결 테스트 (1k)
locust -f load_tests/locustfile_sse_1k.py --headless -u 1000 -r 50 \
  --host http://localhost:5001 --run-time 300s \
  --csv "results/sse_1k" --html "results/sse_1k_report.html"

# 6. 메모리 측정 (SSE 1k 유지 중)
docker stats --no-stream --format "{{.Name}}\t{{.MemUsage}}" > results/mem_sse_1k.txt

# 7. Prometheus 메트릭 스냅샷
curl -s http://localhost:5001/metrics > results/metrics_snapshot_$(date +%s).txt
```

---

## 8. 실측 후 작성 체크리스트

- [ ] 환경 명세 §1 실측값 기입 (CPU·RAM·OS 실행 결과)
- [ ] §3 API warm/cold 테이블 10종 모두 N=10 측정 완료
- [ ] §4 SSE 지표 5종 측정 완료 (`_emit_at` 메커니즘 네이선 협업 후)
- [ ] §5 DB 쿼리 5종 측정 완료
- [ ] §6 Celery 지표 4종 측정 완료
- [ ] regression-perf.md budget 표와 비교 — 위반 항목 없음 확인
- [ ] 제임스 승인 후 상태 "확정"으로 변경
