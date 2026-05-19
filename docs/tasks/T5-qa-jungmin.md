# Task T5 → 정민 (QA · Reviewer)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-26 EOD (E2E 시나리오 + 보안 체크리스트 초안), 이후 상시 게이트
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [결정 메모](../decisions/2026-05-19-realtime-task-queue-dashboard.md)

## 목적

E2E 시나리오 8건 + 보안 audit + 회귀 게이트를 정의하고, 마크 PR 마다 머지 게이트를 운영. **E2E·코드 품질 축의 게이트키퍼**.

## 스코프

### A. E2E 시나리오 8건 (`docs/qa/scenarios.md`)

각 시나리오: `Given / When / Then`, 사전 데이터, 검증 포인트, 실패 시 분류(P0/P1/P2).

| # | 시나리오 | 핵심 검증 |
|---|---|---|
| 1 | 로그인·로그아웃·세션 만료 | 쿠키 속성·CSRF·revokeAllFor |
| 2 | 작업 제출 → running → succeeded 풀 경로 | SSE `job.submitted→started→progress→succeeded` 4종 모두 도착 |
| 3 | 작업 실패 + 자동 재시도 (1s→4s→16s) → failed 확정 | 재시도 카운트, `error` 마스킹 |
| 4 | 작업 취소 (pending/running 두 경우) | Celery revoke, 상태 전이 단방향 |
| 5 | 작업 재시도 (PATCH retry) | 신규 jobs 행 + `retried_to_job_id` |
| 6 | Idempotency-Key 중복 제출 | 동일 키 재요청은 기존 jobs 200 반환, PG UNIQUE + Redis 락 |
| 7 | SSE 끊김 → 자동 재연결 + Last-Event-ID 백필 | 끊김 60초 동안 발생한 이벤트 누락 없음 |
| 8 | 멀티 인스턴스 sampler 단일 리더 | 두 API 인스턴스 동시 가동 시 `queue.counts/workers` 가 중복 발행되지 않음 (`heartbeat:queue_emitter` 락) |

### B. 보안 Audit (`docs/qa/security-audit.md`)

- OWASP A01~A10 각 항목에 대해 마크 구현 PR 별 체크리스트.
- 인증 실패·CSRF 실패·rate limit 동작 자동 확인.
- 비밀번호·세션·CSRF 토큰 **로그 금지** 검증 (로그 grep).
- IDOR — `/api/jobs/:id`, `/api/events/jobs/:id` 모두 소유자 검증.
- argon2id 파라미터 (memory=64MB / iter=3 / parallelism=1) 강제.
- 보안 헤더 (HSTS·X-Content-Type-Options·Referrer-Policy·CSP) 응답 검증.

### C. 회귀 시나리오 (`docs/qa/regression.md`)

- 작업 상태 머신 5단계 (`pending→running→succeeded|failed|canceled`) 위배 시도.
- `succeeded`/`failed`/`canceled` 에서 재진입 시도 거절.
- CSRF 토큰 누락·불일치 → 403 CSRF_FAILED.
- 로그인 5 req/min/IP rate limit.
- 1k 동시 작업 안정 (카맥과 협업, 회귀 환경에서 가벼운 변형 1회).

### D. PR 머지 게이트 운영 규칙

- 정민이 마크 PR 마다 다음 게이트 실행 후 코멘트.
  - 단위/통합 테스트 통과 + 커버리지 ≥ 80% (pytest-cov, vitest).
  - 정적분석 — `ruff`, `pyright`, `eslint`, `tsc --noEmit` 모두 통과.
  - 보안 체크리스트 → CRITICAL/HIGH 0건.
  - E2E 관련 시나리오 통과 (해당 PR 영역).
- 평가 등급: CRITICAL → 머지 차단 / HIGH → 머지 차단 / MEDIUM → 코멘트 후 머지 허용 / LOW → 노트.
- 리뷰 로그 — `docs/qa/review-log.md` 에 PR 단위 표 갱신.

### E. 디자인 시스템 게이트 (수영 인계)

- 색 대비 7쌍 자동 검증 (axe-core + Playwright a11y 스캔). 미달 시 차단.
- 포커스 링 외곽선 제거(`outline: none`) 발견 시 차단.

## 산출물

- `docs/qa/scenarios.md`, `docs/qa/security-audit.md`, `docs/qa/regression.md`, `docs/qa/review-log.md`.
- E2E 자동화 — Playwright 권장. `tests/e2e/*.spec.ts` 마크가 작성, 정민이 시나리오 정의·리뷰.

## 완료 조건

- 8개 시나리오 명세 작성 (마크 구현 직전).
- 보안 체크리스트 OWASP A01~A10 작성.
- 첫 마크 PR 머지 게이트 운영 시작.

## 회신 방법

시나리오·체크리스트 초안 완료 시 `team-send 제임스 "[결과] T5 E2E·security·regression 초안 완료"` 회신. 이후 PR 게이트 통과 또는 차단은 정민 → 마크 직접 송신.
