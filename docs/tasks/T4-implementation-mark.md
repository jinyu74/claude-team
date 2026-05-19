# Task T4 → 마크 (Developer)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-26 EOD (Phase 1 / M1)
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [결정 메모](../decisions/2026-05-19-realtime-task-queue-dashboard.md), [UI 인벤토리](../analysis/ui-inventory.md), [리서치](../analysis/research-realtime-stack.md)

## 목적

ADR-001 의 Phase 1 (M1) 골격을 구현. **E2E 가 가능한 최소 동작 시스템**.

## 스코프 (M1 만)

### BE — Python + Flask + Celery

1. **저장소·도구 초기화**
   - `pyproject.toml` (Poetry 또는 uv). `ruff` + `pyright` + `pytest` + `pytest-cov`.
   - `docker-compose.yml` — Postgres 16, **Redis 7.4.2** (R-006 명시), Flask, Celery, Flower(dev).
   - Redis: `requirepass`, `bind 127.0.0.1` (Compose 네트워크 한정), `FLUSHALL`/`CONFIG` `rename-command ""`.
2. **DB 스키마 + Alembic**
   - ADR §4.1 `users` / `jobs` / `job_events` 그대로. UNIQUE/CHECK/인덱스 모두.
   - 첫 마이그레이션 1개로 통합.
3. **Flask 골격**
   - blueprint 분할 — `auth`, `api_me`, `api_jobs`, `api_events`, `internal_metrics`, `healthz`.
   - 미들웨어: 세션 검증, CSRF (double-submit), 요청별 `X-Request-Id`, JSON 오류 핸들러.
   - 보안 헤더: `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy`, CSP.
4. **인증**
   - `argon2id` 해시. `sid` 쿠키 14d 슬라이딩.
   - `csrf:<sid>` Redis 키. `X-CSRF-Token` 헤더 검증.
   - `revokeAllFor` 구현 (`user_sids:<user_id>` SET).
5. **작업 API**
   - 엔드포인트 표(ADR §5.1) 10개 모두. `Idempotency-Key` 처리(`jobs.idempotency_key` UNIQUE + Redis 60s 락).
   - `PATCH /api/jobs/:id` 취소(Celery `revoke`) / 재시도(신규 행 + `retried_to_job_id`).
6. **Celery + 더미 작업**
   - 큐 `high`, `default`. 워커 `-Q high,default`. `acks_late=True`, `task_reject_on_worker_lost=True`.
   - 더미 작업 1개: `dummy.sleep(seconds: int, fail_prob: float)`. 5 ~ 30초 sleep, `fail_prob` 으로 비결정적 실패.
   - 재시도: `autoretry_for=(TransientError,)`, `retry_backoff=True`, `max_retries=3`.
   - 상태 전이마다 `job_events` INSERT + Redis publish (사용자 채널) + XADD (Stream).
7. **SSE 핸들러**
   - `GET /api/events/jobs` — 사용자 채널. SUBSCRIBE `events:jobs:user:<uid>` + `events:jobs:user:<uid>:stream` 백필 + `events:system:queue` 다중 SUBSCRIBE.
   - `GET /api/events/jobs/:id` — 작업 상세 채널. 소유자 검증 후 `events:jobs:job:<jid>` SUBSCRIBE.
   - `Last-Event-ID` 헤더로 Stream 백필 (최대 100건 또는 60초).
   - keep-alive `: ping\n\n` 15초마다.
8. **시스템 sampler**
   - 단일 리더 락 `heartbeat:queue_emitter` `SET NX EX 10` 보유 인스턴스가 1s/5s 주기 publish.
   - `queue.counts` — PG `jobs` 상태별 카운트, 동일값 skip.
   - `queue.workers` — Celery `inspect()` 결과, throughput = 직전 60s succeeded+failed 합 ÷ 60.
9. **관측성**
   - 구조화 JSON 로그 (ADR §7.1 필수 필드).
   - `/metrics` Prometheus 텍스트 (§7.2 메트릭 카탈로그 전부).
   - `X-Request-Id` → Celery payload `_trace_id` 전파.

### FE — React + TypeScript + Vite

1. **저장소·도구**
   - `vite` + `react` + `typescript` + `eslint` + `prettier`. CSS는 vanilla + 토큰(`tokens.css`).
   - `tokens.css` — 수영의 `ui-tokens.md` 그대로. **라이트 모드 미디어 + selector 콤마 무효 부분은 두 블록으로 분리**.
   - 테스트: `vitest` + `@testing-library/react`.
2. **컴포넌트 (M0 + M1)**
   - M0: `Button`, `Input`, `PasswordInput`, `StatusBadge`, `PageLayout`, `AppHeader`, `ErrorMessage`.
   - M1: `LoginForm`, `QueueStatusCard`, `WorkerStatusCard`, `JobCard`, `ProgressIndicator`, `JobList`, `SSEConnectionBanner`.
3. **데이터 레이어**
   - `fetch` 래퍼 — CSRF 헤더 자동 부착, 401 시 로그인 화면 리다이렉트.
   - SSE 클라이언트 — `EventSource` 래퍼, `addEventListener('job.submitted'|'job.started'|...)`, 끊김 시 자동 재연결 + 배너 표시.
   - 상태: 서버 상태는 `EventSource` 이벤트 기반 in-memory store (zustand 또는 그에 준하는 경량 store). 서버 상태와 클라 상태 분리.
4. **a11y**
   - `ToastRegion` 단일 라이브 리전, `Toast` 개별 `role="status|alert"`.
   - 모든 인터랙티브 요소 `focus-visible` 외곽선 유지, `outline: none` 금지.
   - `prefers-reduced-motion: reduce` 시 `duration-*` 토큰 0ms.

### 테스트

- **단위**: 모든 BE 유틸·검증·해시·CSRF·이벤트 직렬화. 모든 FE 유틸·hook.
- **통합**: 인증(login/logout/revokeAll), 작업 제출/취소/재시도, idempotency, SSE 연결+이벤트 수신, 시스템 sampler 단일 리더.
- **커버리지**: ≥ 80% (pytest-cov, vitest --coverage). 미달 시 미머지.

## 산출물

- `apps/api/` (Flask + Celery + Alembic) `apps/web/` (Vite + React) `infra/docker-compose.yml`
- PR 1 ~ 4 (블루프린트 단위 분할 권장). 모든 PR 본문에 ADR-001 §섹션 인용.
- 인터페이스 변경 PR 은 `interface-change` 라벨 + 영향 분석 — 네이선 승인 필수.

## 완료 조건

- 정민 E2E 시나리오 8건(T5) 통과.
- 정민 리뷰 CRITICAL/HIGH 0건.
- 카맥 perf budget(T6) 통과: API p95 < 200ms, SSE 푸시 지연 p95 < 500ms, 1k 동시 안정.
- 커버리지 ≥ 80%.

## 제약

- ADR §4 / §5 / §6 변경은 네이선 승인 필수 (§8 절차). 새 이벤트/메트릭 추가 시 §5.4 / §7.2 표 갱신 동반 PR.
- 비밀번호·세션·CSRF 토큰 로그 금지.
- TDD 우선 — 테스트부터 작성.

## 회신 방법

블루프린트 PR 단위로 마무리 시 `team-send 제임스 "[결과] T4 Phase 1.<n> PR #N 완료"` 회신. 정민/카맥에 게이트 요청은 마크가 직접 송신.
