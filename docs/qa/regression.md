# 회귀 시나리오 — 실시간 작업 큐 대시보드 (M1)

- 최종 갱신: 2026-05-19 by 정민
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [scenarios.md](scenarios.md), [security-audit.md](security-audit.md), [T5](../tasks/T5-qa-jungmin.md)
- 실행 주기 — PR 별: 영향 범위 항목만. 주간 batch: 전체. `develop/<product>/<version>` → `main` 머지 직전: 전체 1회 풀.

## 0. 사용 방법

본 문서는 E2E 시나리오([scenarios.md](scenarios.md)) 와 보안 audit([security-audit.md](security-audit.md)) 으로는 잡히지 않는 **회귀 한정 위협** 을 다룬다. 카맥의 perf 회귀(`docs/performance/regression-perf.md`) 와는 분리.

평가 등급은 audit 과 동일 — CRITICAL/HIGH → 머지 차단, MEDIUM → 코멘트 후 머지 허용, LOW → 노트.

## 0.1 분류 색인

| 영역 | 항목 수 | 위치 |
|---|---|---|
| 1. 상태 머신 단방향성 | 6 | §1 |
| 2. CSRF | 4 | §2 |
| 3. Rate Limit | 3 | §3 |
| 4. 인증/세션 | 4 | §4 |
| 5. SSE 백필·재연결 | 4 | §5 |
| 6. Idempotency | 3 | §6 |
| 7. 멀티 인스턴스·1k 동시 | 3 | §7 (카맥 협업) |

---

## 1. 작업 상태 머신 단방향성

> ADR-001 §4.3: `pending → running → succeeded | failed | canceled` 단방향. 모든 종결 상태에서 재진입 금지.

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 (위반 시) | 상태 |
|---|---|---|---|---|---|
| SM-1 | `succeeded` 작업에 `PATCH {status:"canceled"}` | `409 INVALID_TRANSITION` + `{error:{code:"INVALID_TRANSITION", message:"cancel not allowed from succeeded"}}`, status 불변 | `tests/regression/state-machine.spec.ts:succeeded-no-cancel` | **CRITICAL** | ⚠️ 미작성 |
| SM-2 | `failed` 작업에 `PATCH {status:"canceled"}` | `409 INVALID_TRANSITION` + `"cancel not allowed from failed"`, status 불변 | `:failed-no-cancel` | **CRITICAL** | ⚠️ 미작성 |
| SM-3 | `canceled` 작업에 `PATCH {action:"retry"}` (시나리오 5 의 정상 경로) | `200` + 신규 jobs 행 | 시나리오 5 와 중복 | HIGH | ✅ scenarios.md #5 |
| SM-4 | `succeeded` 작업에 `PATCH {action:"retry"}` | `409 INVALID_TRANSITION` + `{error:{code:"INVALID_TRANSITION", message:"retry not allowed from succeeded"}}`. **ADR-001 Patch 3 (§3.2·§4.3·§5.1) 확정** — `failed`/`canceled` 만 retry 허용. `succeeded` 재실행은 후속 ADR 의 `clone` 액션 (M1 외) | `:retry-on-succeeded` | HIGH | ✅ ADR Patch 3 머지됨. ⚠️ 자동화 미작성 |
| SM-5 | `running` 또는 `pending` 작업에 `PATCH {action:"retry"}` (아직 종결 X) | `409 INVALID_TRANSITION` + `"retry not allowed from <status>"` (ADR §3.2 — 자동 재시도가 우선) | `:retry-non-finalized` | HIGH | ⚠️ 미작성 |
| SM-6 | DB 직접 조작으로 `succeeded → running` 강제 후 워커 동작 (방어적 검증) | 워커가 `event_ulid` UNIQUE 위반 또는 status 검증 실패로 reject. 사용자 응답에는 영향 없음 | `:db-tampering-guard` | MEDIUM | ⚠️ 미작성 |

**메모.** SM-6 는 운영 시나리오가 아니라 **방어 깊이 확인용**. DB 가 손상되었을 때 워커가 cascade fail 하지 않는지를 본다. SQLAlchemy 모델의 `status` 변경 시 transition validator 메서드 권장.

---

## 2. CSRF (double-submit)

> ADR-001 §6.3: 상태 변경 메서드에 한해 double-submit. `csrf:<sid>` 와 헤더 `X-CSRF-Token` 일치 검증.

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| CSRF-1 | `POST /api/jobs` `X-CSRF-Token` 헤더 누락 | `403 CSRF_FAILED` | `tests/regression/csrf.spec.ts:missing-header` | HIGH |
| CSRF-2 | `X-CSRF-Token` 헤더값 변조 (1글자 변경) | `403 CSRF_FAILED` | `:mismatched-token` | HIGH |
| CSRF-3 | 사용자 A 의 토큰을 사용자 B 의 쿠키와 함께 사용 | `403 CSRF_FAILED` (세션 바인딩) | `:cross-session-token` | **CRITICAL** |
| CSRF-4 | SSE `GET /api/events/jobs` 에 CSRF 토큰 요구 없음 | `200` (GET 은 CSRF 대상 외, ADR §6.3) | `:get-no-csrf` | LOW (음성 검증) |

---

## 3. Rate Limit

> ADR-001: 로그인 5 req/min/IP. 추가 라우트는 M1 범위 외.

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| RL-1 | `POST /auth/login` 동일 IP 6회 연속 발사 (모두 잘못된 비밀번호) | 6번째 응답 `429 RATE_LIMITED` + `Retry-After: <초>` 헤더 | `tests/regression/rate-limit.spec.ts:login-5-per-min` | HIGH |
| RL-2 | 정확한 비밀번호로 6번째 시도 | `429` 유지 — 정상 비밀번호여도 limit 적용. 1분 경과 후 정상 처리 | `:limit-applies-even-on-success` | HIGH |
| RL-3 | 두 다른 IP 에서 각 5회 | 양쪽 모두 통과. limit 이 IP 별로 격리 | `:per-ip-isolation` | MEDIUM |

**구현 메모.** Redis 기반 sliding window 또는 token bucket. `tests/regression/rate-limit.spec.ts` 는 Playwright 의 `--ip` mock 또는 Flask 의 `X-Forwarded-For` 신뢰 헤더로 IP 분리.

---

## 4. 인증·세션

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| AUTH-1 | `sid` 쿠키를 임의 ULID 로 변조 | `401 UNAUTHENTICATED` (서버 측 `sid:*` 조회 실패) | `tests/regression/auth.spec.ts:sid-forge` | **CRITICAL** |
| AUTH-2 | 만료된 `sid` (Redis TTL 만료) 로 요청 | `401`. `revokeAllFor` 후와 동일 응답 코드/메시지 (정보 누설 없음) | `:expired-sid` | HIGH |
| AUTH-3 | 두 사용자가 동시에 같은 ULID `sid` 충돌 (이론적 확률 0 이지만 강제 충돌 시) | 두 번째 요청은 `401` (서버는 sid → user_id 매핑이 1:1) | `:sid-collision-guard` | MEDIUM |
| AUTH-4 | `Cookie: sid=01J...; sid=01K...` (멀티 쿠키) 보낸 경우 | **Flask 기본(첫 번째 sid)** 신뢰. 첫 sid 가 유효하면 `200`, 무효면 `401`. 두 번째 sid 는 무시 (검증조차 안 함) | `:multi-cookie-first-wins` | MEDIUM |

**CTO 답변 확정 (2026-05-19, Q-R2).** Flask 기본 동작 따름. 명시 거부 정책은 정상 클라이언트 영향 위험. 충돌 시 검증 실패로 자연스럽게 401 처리되므로 보안상 추가 위험 없음. [review-log.md](review-log.md) 영역별 게이트 적용 표에 인증·세션 행 비고 한 줄 추가됨.

---

## 5. SSE 백필·재연결

> ADR-001 §2.4 / §2.5 / §5.4.2: Last-Event-ID 백필, Redis Stream MAXLEN/TTL.

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| SSE-1 | `Last-Event-ID` 가 stream MAXLEN/TTL 을 초과한 오래된 ID (시나리오 7 의 step 8) | 서버는 `event: catchup_overflow` 발행 → 클라이언트가 풀 리프레시 트리거 | `tests/regression/sse.spec.ts:overflow` | HIGH |
| SSE-2 | API 가 Redis 와 일시 단절 후 복구 | SSE 핸들러가 SUBSCRIBE 재시도. 클라이언트는 정중 종료(`event: bye`) 후 EventSource 표준 재연결 | `:redis-blip` | HIGH |
| SSE-3 | 1시간 정중 종료 → 자동 재연결 (ADR §2.4) | 사용자 액션 없이도 정상 재접속. `Last-Event-ID` 로 백필 1회 | `:hourly-graceful-close` | MEDIUM |
| SSE-4 | 동일 사용자 5개 탭 동시 구독 | 5개 EventSource 모두 동일 이벤트 수신. Redis pub/sub 가 fanout. 메트릭 `sse_clients_active{channel="user"}` = 5 | `:multi-tab-fanout` | MEDIUM |

**메모.** SSE-2 는 Redis 컨테이너 `docker pause/unpause` 또는 toxiproxy 로 인위적 단절 → 30초 내 복구.

---

## 6. Idempotency

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| IDEM-1 | PG `idempotency_key` UNIQUE 위반 동시 INSERT (Redis 락이 5초 만료된 직후 같은 키로 두 요청) | 정확히 1건 성공, 1건 `409 IDEMPOTENCY_CONFLICT`. 5xx 없음 | `tests/regression/idempotency.spec.ts:race-after-lock-expiry` | HIGH |
| IDEM-2 | retry 신규 행이 원본의 `idempotency_key` 와 충돌하지 않음 (마크가 새 ULID 발급) | UNIQUE 위반 없이 신규 행 생성 | `:retry-new-key` | HIGH |
| IDEM-3 | `Idempotency-Key` 가 ULID 형식이 아닌 임의 문자열 (예: `<script>alert(1)</script>`) | 서버는 검증 후 `400 VALIDATION_FAILED` 또는 그대로 저장 (XSS 위험은 출력 escape 로 방어). 어느 정책이든 명시 + 일관 | `:malformed-key` | MEDIUM |

---

## 7. 부하·멀티 인스턴스 (카맥 협업)

> 본 섹션은 카맥의 perf 회귀(`docs/performance/regression-perf.md`) 와 **공동 운영**. perf 게이트 미달 + 본 항목 동시 충족이 머지 조건.

| ID | 회귀 케이스 | 기대 동작 | 자동화 위치 | 등급 |
|---|---|---|---|---|
| LOAD-1 | **1k 동시 작업** (작업당 `seconds:1` ~ `seconds:3`) 제출 → 모두 종결 | 5분 내 모두 `succeeded|failed|canceled` 종결. 5xx 비율 ≤ 0.1%. 카맥의 p95 게이트 충족 | `tests/load/1k_jobs.py` (**locust** 통일). 정민이 시나리오 검수 | HIGH |
| LOAD-2 | 1k 동시 부하 중 SSE 사용자 채널 끊김 ≤ 1% | recorder 가 keep-alive ping 15s 주기로 정상 수신 | `tests/load/1k_sse.py` (**locust**) | HIGH |
| LOAD-3 | 멀티 인스턴스 (API 2개) 환경에서 sampler 중복 발행 0 (시나리오 8 의 회귀 변형) | `heartbeat:queue_emitter` 락 충돌 시 1개 인스턴스만 emitter | `tests/regression/multi-instance-leader.spec.ts` (시나리오 8 자동화와 공유) | HIGH |

**도구 통일 (Q-R3 CTO 답변 확정, 2026-05-19).** LOAD-1/LOAD-2 는 **locust** 사용. 카맥 T6 의 `docs/performance/load-tests.md §3·§4` 와 동일 도구로 학습·운영 비용 절감. SSE 측 부하는 locust `User` 의 `on_start` 에서 `sseclient-py` 또는 `httpx` 비동기 stream 으로 구독 (카맥과 패턴 통일).

**운영 규칙.**
- LOAD-1/2 는 **주간 batch** 또는 `develop → main` 머지 직전 1회. 일반 PR 마다는 실행 안 함 (시간 비용).
- LOAD-3 는 sampler 코드 변경 PR 마다 실행.

---

## 회귀 게이트 실행 매트릭스

| 트리거 | 실행 대상 |
|---|---|
| 일반 마크 PR (해당 영역 변경) | §1·§2·§3·§4·§5·§6 중 영향 범위 항목 |
| 인증·세션 변경 PR | §2·§4 전체 + §1 SM-1/SM-2 |
| 큐·상태 머신 변경 PR | §1 전체 + §6 |
| SSE 변경 PR | §5 전체 + §7 LOAD-3 |
| 주간 batch (정민, 매주 화요일) | §1~§6 전체 + §7 LOAD-1/LOAD-2 |
| `develop/<product>/<version>` → `main` 머지 PR | 전체 1회 풀 + 시나리오 1~8 풀 + 카맥 perf 게이트 + 보안 audit 전체 |

---

## 사전 합의 사항

### CTO 답변 확정 (2026-05-19, [inspection-T5-jungmin.md](inspection-T5-jungmin.md))

- ~~**Q-R1.** SM-4 정책.~~ → **(b) `failed`/`canceled` 만 retry 허용** (의미적 정합). `succeeded` 재실행은 후속 "clone" 액션. ADR-001 Patch 3 (네이선) 머지 후 SM-4 자동화 활성. ✅ 반영 완료.
- ~~**Q-R2.** AUTH-4 멀티 sid 정책.~~ → **Flask 기본 (첫 번째 sid)** 따름. ✅ 반영 완료.
- ~~**Q-R3.** LOAD 도구 선택.~~ → **locust 통일** (카맥 T6 와 일치). 파일 확장자 `.py` 로 변경. ✅ 반영 완료.

### 외부 의존

- **ADR-001 Patch 3 (네이선)** — `succeeded` retry 불가 명시. Patch 3 머지 후 SM-4 자동화는 HIGH 게이트로 활성. Patch 3 미머지 상태에서 마크 PR 이 도착하면 SM-4 만 P2 (스펙 불일치) 로 임시 분류.
- **카맥 T6 (`docs/performance/load-tests.md`)** — locust User 클래스·헬퍼 재사용. 정민의 LOAD-1/LOAD-2 는 카맥의 부하 패턴 위에 회귀 시나리오만 얹는 형태. 카맥 산출물 도착 시 정민이 검수.

---

## 자동화 인덱스 (요약)

| 파일 | 대응 항목 | 작성 |
|---|---|---|
| `tests/regression/state-machine.spec.ts` | SM-1·2·4·5·6 | 마크 |
| `tests/regression/csrf.spec.ts` | CSRF-1·2·3·4 | 마크 |
| `tests/regression/rate-limit.spec.ts` | RL-1·2·3 | 마크 |
| `tests/regression/auth.spec.ts` | AUTH-1·2·3·4 | 마크 |
| `tests/regression/sse.spec.ts` | SSE-1·2·3·4 | 마크 |
| `tests/regression/idempotency.spec.ts` | IDEM-1·2·3 | 마크 |
| `tests/regression/multi-instance-leader.spec.ts` | LOAD-3, 시나리오 8 | 마크 |
| `tests/load/1k_jobs.py` (locust) | LOAD-1 | 마크 + 카맥 검수 |
| `tests/load/1k_sse.py` (locust) | LOAD-2 | 마크 + 카맥 검수 |
