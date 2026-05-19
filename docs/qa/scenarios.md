# E2E 시나리오 — 실시간 작업 큐 대시보드 (M1)

- 최종 갱신: 2026-05-19 by 정민
- 상위: [ADR-001](../decisions/ADR-001-architecture.md), [T5](../tasks/T5-qa-jungmin.md)
- 자동화 대상: `tests/e2e/*.spec.ts` (Playwright). 시나리오 정의·리뷰는 정민, 자동화 코드 작성은 마크.
- 회귀 환경 변형: [regression.md](regression.md) 참조.

## 0. 공통

### 0.1 분류 기준 (P0 / P1 / P2)

| 등급 | 정의 | 조치 |
|---|---|---|
| **P0** | 핵심 기능 망실 (작업 제출/실행/상태 푸시/인증 중 하나 실패) | 머지 차단, 즉시 mark·정민 동시 알림 |
| **P1** | 정상 경로는 동작하나 보안·정합성·UX 회귀 (CSRF/IDOR/SSE 백필 누락) | 머지 차단, 동일 PR 내 수정 |
| **P2** | 보조 경로·메시지 문구·로깅 누락 | 코멘트 후 머지 허용 (후속 Sub-task) |

### 0.2 사전 데이터 표준 시드

각 시나리오는 다음 시드 위에서 동작 (마크가 `tests/e2e/fixtures.ts` 에 일관 제공).

- 사용자 A — `alice@example.com` / 비밀번호 `Alice!Pass-2026` (argon2id 해시 저장)
- 사용자 B — `bob@example.com` / 비밀번호 `Bob!Pass-2026` (IDOR 검증용)
- 더미 작업 타입 — `dummy.sleep` (payload `{seconds:int, fail?:bool, transient?:bool}`)
  - `seconds` : 워커가 sleep 후 succeed
  - `fail:true` : PermanentError 로 즉시 failed
  - `transient:true` : TransientError 3회 → 재시도 1s→4s→16s

### 0.3 표준 SSE 수집기

E2E 는 `EventSource` 를 직접 구독하지 않고 `tests/e2e/lib/sse-recorder.ts` 의 `recordEvents(url, sessionCookie, opts)` 를 사용한다 (마크 구현). recorder 는 다음을 보장.

- 이벤트 수신 시 `{id, event, data, receivedAt}` 배열에 push.
- `untilEvent(type)` / `untilEventsCount(n)` Promise 헬퍼 제공.
- 연결 종료/재연결을 명시 API 로 노출 (시나리오 7 에서 사용).

---

## 시나리오 1 — 로그인 · 로그아웃 · 세션 만료 / revokeAllFor (P0)

**검증 포인트.** 쿠키 속성(HttpOnly/Secure/SameSite=Lax/Path=/) · CSRF double-submit · `DELETE /auth/sessions` 의 revokeAllFor · 만료 후 401 + 재로그인 유도.

### Given
- 사용자 A 만 시드. 활성 세션 없음.
- 환경 변수 `SESSION_ABS_TTL_OVERRIDE_SEC=5` (E2E 전용. 운영은 14d).
  - 마크는 환경변수 가드를 `if NODE_ENV in (test, ci)` 로 한정. 운영 빌드는 무시.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | `POST /auth/login {email:"alice@...", password:"Alice!Pass-2026"}` | `204` + `Set-Cookie: sid=...` (HttpOnly/Secure/SameSite=Lax/Path=/) — 4 속성 모두 검사 |
| 2 | `GET /api/me` | `200 {userId, email, csrfToken}` — `csrfToken` 존재 |
| 3 | `POST /api/jobs` **CSRF 헤더 누락** | `403 {error:{code:"CSRF_FAILED"}}` (P1 차단) |
| 4 | `POST /api/jobs` **정상 CSRF 헤더 + Idempotency-Key** | `201 {job}` |
| 5 | 사용자 A 가 두 번째 브라우저 컨텍스트에서 로그인 | 두 sid 모두 `user_sids:<uid>` 에 존재 |
| 6 | `DELETE /auth/sessions` (revokeAllFor) | `204` |
| 7 | 첫 컨텍스트로 `GET /api/me` | `401 {error:{code:"UNAUTHENTICATED"}}` |
| 8 | 두 번째 컨텍스트로 `GET /api/me` | `401` (둘 다 revoke) |
| 9 | 다시 `POST /auth/login` 후 5초 대기 (절대 만료 override) → `GET /api/me` | `401` |

**실패 분류.** 1·4·6 미통과 = P0. 3·5·7·8 미통과 = P1. 쿠키 속성 1종 누락 = P1 (CSRF/세션 무력화). `csrfToken` 누락 = P0.

**구현 메모 (마크).** `tests/e2e/auth.spec.ts` 에서 Playwright `context.cookies()` 로 4 속성을 직접 비교. `SESSION_ABS_TTL_OVERRIDE_SEC` 미구현 시 step 9 는 sid TTL 을 Redis CLI 로 만료시키는 헬퍼로 대체 가능.

---

## 시나리오 2 — 작업 제출 → running → succeeded 풀 경로 (P0)

**검증 포인트.** SSE 사용자 채널에 `job.submitted → job.started → job.progress → job.succeeded` **4종 모두** 도착. PG `jobs.status` 단방향 전이. `job_events` 행 4건 이상 INSERT. `started_at`/`finished_at` 채워짐.

### Given
- 사용자 A 로그인. SSE recorder 가 `/api/events/jobs` 구독.
- 작업 페이로드: `{type:"dummy.sleep", payload:{seconds:3, progress:[0.33, 0.66]}}`.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | `POST /api/jobs` (with Idempotency-Key) | `201 {job.status:"pending"}` |
| 2 | recorder.untilEvent(`job.submitted`) (timeout 1s) | data.jobId = step 1 응답 id |
| 3 | recorder.untilEvent(`job.started`) (timeout 2s) | data.attempts = 1, data.startedAt 존재 |
| 4 | recorder.untilEvent(`job.progress`) ≥ 1건 (timeout 5s) | 0 < progress ≤ 1, 사용자 채널은 **1s throttle** 이므로 최소 1건만 보장 |
| 5 | recorder.untilEvent(`job.succeeded`) (timeout 6s) | data.finishedAt 존재 |
| 6 | `GET /api/jobs/{id}` | status=`succeeded`, attempts=1, finishedAt≠null, error=null |
| 7 | `GET /api/jobs/{id}` 의 recentEvents | 최소 4건 (`submitted`,`started`,`progress`,`succeeded`) 모두 포함, 순서 보존 |
| 8 | SSE `id:` 필드는 모두 ULID 형식 | event_ulid 단조증가 (정렬 확인) |

**실패 분류.** 어느 이벤트라도 누락 = P0. progress 가 사용자 채널에 0건 도착 = P1 (throttle 의 1초 이상 지속 작업이므로 1건은 와야 함). 8 미통과 = P1 (백필 정합성 위반).

**구현 메모 (마크).** `dummy.sleep` 워커는 `seconds` 동안 N등분하여 `progress` 이벤트를 발행 (테스트에서 결정적). `payload.progress` 배열로 발행 비율을 지정.

---

## 시나리오 3 — 작업 실패 + 자동 재시도 (1s → 4s → 16s) → failed 확정 (P0)

**검증 포인트.** TransientError 3회 재시도 → `failed` 확정. `attempts` 카운트 정확. `error` 메시지가 stack trace·내부 경로를 노출하지 않음 (마스킹). 백오프 지수 패턴 (jitter 허용 범위).

### Given
- 사용자 A 로그인. recorder 구독.
- 페이로드: `{type:"dummy.sleep", payload:{seconds:1, transient:true}}` — 워커가 매번 `TransientError("upstream timeout")` 를 raise.
- E2E 시간 단축 override: `CELERY_BACKOFF_BASE_SEC=0.1` (운영 1s 의 1/10). 비율은 유지 → 0.1 → 0.4 → 1.6.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | `POST /api/jobs` | `201` |
| 2 | recorder.untilEvent(`job.started`) ×4 (1 회 최초 + 3 회 재시도) | attempts 가 1,2,3,4 단조증가 |
| 3 | 인접 `started` 간 wall-clock 간격 | t2-t1 ≈ 0.1s ±50ms / t3-t2 ≈ 0.4s ±100ms / t4-t3 ≈ 1.6s ±300ms (jitter ±25%) |
| 4 | recorder.untilEvent(`job.failed`) (timeout 5s) | data.error 가 사용자용 짧은 문구 (예: `"transient error"`). 50자 이내. stack/path/secret 미포함 |
| 5 | `GET /api/jobs/{id}` | status=`failed`, attempts=4, error 동일하게 마스킹 |
| 6 | PG `job_events` 조회 (테스트 헬퍼) | type=`started` 4건, type=`failed` 1건 |
| 7 | 로그 grep — `tests/e2e/lib/log-tail.ts` 로 worker 로그 1회 캡처 | `error.message` 는 짧음, `error.stack` 은 **내부 로그에만** 존재. SSE 응답 본문에는 stack 키 자체가 없음 |

**실패 분류.** 4·5 미통과 = P0. 3 간격 ±100% 초과 = P1 (백오프 비율 회귀). 4 의 error 가 stack/secret 포함 = **CRITICAL → 머지 차단**.

**error 마스킹 규칙 (재확인).** 마크 구현은 다음을 보장.
- `error.message` ≤ 200자 (응답·이벤트 모두).
- `error.stack` 은 응답·이벤트에 **절대 포함 금지** (내부 로그 전용).
- 정민의 `tests/e2e/lib/assertions.ts` 의 `expectNoLeak(error)` 헬퍼로 secret 패턴(`password`, `secret`, `token`, `Bearer `, `/Users/`, `/home/`, `Traceback`) 부재 검증.

---

## 시나리오 4 — 작업 취소 (pending / running 두 경우) (P1)

**검증 포인트.** `PATCH /api/jobs/:id {status:"canceled"}` 가 두 단계에서 모두 단방향 전이. pending → canceled 는 워커 pick 전, running → canceled 는 Celery revoke + best-effort. 종결 상태에서 재취소 시도 거절.

### Given
- 사용자 A 로그인. recorder 구독.
- 두 작업을 순차 제출 — Job-P (`seconds:30`, 큐 길이를 키워 pending 으로 머물게), Job-R (`seconds:30`, 워커 pick).
- 동시성 제어 — 마크는 큐를 다음과 같이 셋업.
  1. 워커 동시성 1로 시작.
  2. Job-R 제출 → recorder.untilEvent(`job.started`) 대기.
  3. Job-P 제출 → 워커가 바쁘므로 `pending`.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | Job-P (pending) `PATCH /api/jobs/{P} {status:"canceled"}` + CSRF | `200 {job.status:"canceled"}` |
| 2 | recorder.untilEvent(`job.canceled`) for P | data.jobId = P, finishedAt 존재 |
| 3 | Job-R (running) `PATCH /api/jobs/{R} {status:"canceled"}` + CSRF | `200 {job.status:"canceled"}` |
| 4 | recorder.untilEvent(`job.canceled`) for R | 5s 이내 도착 (best-effort) |
| 5 | 종결된 Job-P `PATCH ... {status:"canceled"}` 재시도 | `409 {error:{code:"INVALID_TRANSITION", message:"cancel not allowed from canceled"}}` (ADR Patch 3) |
| 6 | `GET /api/jobs/{R}` | status=`canceled`, finishedAt≠null |
| 7 | 워커 로그 grep | `revoke` 발행 로그 1건. SIGTERM/SIGUSR 협조 시도 흔적 |
| 8 | Job-R 가 우연히 step 3 직전에 succeeded 된 경우 (레이스) | `200 {job.status:"succeeded"}` 또는 `409`. **둘 다 허용** — 단, status 가 `canceled` 로 되돌아가지는 않음 |

**실패 분류.** 1·3 미통과 = P0 (양방향 명령 실패). 5 미통과 = P1 (상태 머신 위배). 8 에서 `succeeded → canceled` 전이가 발생하면 **CRITICAL** (단방향 위반).

**구현 메모 (정민).** 8 의 레이스를 안정화하려면 `dummy.sleep` 의 sleep 구간을 명확히 길게(30s) 잡아 step 3 시점에 거의 확실히 running 상태로 만든다. flaky 시 재시도 1회 허용, 2회 연속 실패 시 차단.

---

## 시나리오 5 — 작업 재시도 (PATCH retry) (P1)

**검증 포인트.** `PATCH /api/jobs/:id {action:"retry"}` 가 신규 `jobs` 행을 만들고, 이전 행에 `retried_to_job_id` 가 기록됨. 신규 행은 새 idempotency_key 를 자동 부여하거나 헤더로 받음. SSE `job.retried` 이벤트 발행.

### Given
- 사용자 A 의 실패 종결 작업 Job-F (시나리오 3 의 산출물 또는 새로 셋업).

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | `PATCH /api/jobs/{F} {action:"retry"}` + CSRF + 새 `Idempotency-Key: <ulid>` | `200 {job}` — 응답 `job.id` ≠ F |
| 2 | PG 조회: 신규 행 N | N.status=`pending`, N.user_id=F.user_id, N.type=F.type, N.payload=F.payload |
| 3 | PG 조회: 기존 행 F | F.retried_to_job_id = N.id |
| 4 | recorder.untilEvent(`job.retried`) | data = `{jobId:F, newJobId:N}` |
| 5 | recorder.untilEvent(`job.submitted`) for N | 정상 라이프사이클 진입 |
| 6 | 종결되지 않은 작업 (`pending` 또는 `running`) 으로 retry 시도 | `409 {error:{code:"INVALID_TRANSITION", message:"retry not allowed from <status>"}}` (ADR Patch 3 §3.2) |
| 7 | F 에 대해 다시 retry 시도 (이미 `retried_to_job_id` 설정됨) | `409 {error:{code:"INVALID_TRANSITION", message:"already retried"}}` |

**실패 분류.** 1·2·3 미통과 = P0. 4 누락 = P1 (이벤트 카탈로그 §5.4 회귀). 6·7 미통과 = P1 (상태 정합성). 8 미통과 = HIGH (Q-R1 정합성, ADR-001 Patch 3 대기).

### 추가 검증 — Idempotency-Key 양 경로 (Q-A3 CTO 답변 확정)

CTO 답변 (2026-05-19): retry 시 `Idempotency-Key` 헤더 누락 **허용**. ADR §3.3 — "누락 시 서버가 ULID 생성하여 응답에 포함". E2E 는 양 경로 모두 1회씩 검증.

| Step | When | Then |
|---|---|---|
| 8 | 종결 상태 (`failed`/`canceled`) 작업에 `PATCH {action:"retry"}` + **Idempotency-Key 미동봉** | `200 {job}` — 신규 행 N. 응답 본문에 서버가 생성한 `idempotencyKey` 필드 또는 응답 헤더 `Idempotency-Key: <ulid>` 포함 |
| 9 | step 8 의 응답에서 받은 키를 그대로 재사용해 동일 `PATCH` 호출 | `200 {job:N}` — 동일 행 반환 (멱등). 새 행 만들지 않음 |
| 10 | `succeeded` 작업에 `PATCH {action:"retry"}` (ADR-001 Patch 3 §3.2·§4.3·§5.1) | `409 {error:{code:"INVALID_TRANSITION", message:"retry not allowed from succeeded"}}` |

---

## 시나리오 6 — Idempotency-Key 중복 제출 (P1)

**검증 포인트.** 동일 `Idempotency-Key` 재요청은 기존 `jobs` 행을 200 으로 반환 (201 아님). PG `UNIQUE(user_id, idempotency_key)` 동작. Redis `idem:<uid>:<key>` 짧은 in-flight 락이 동시 요청을 직렬화 (5xx 누수 없음).

### Given
- 사용자 A 로그인. `key = "01J5KZSAMEKEY..."` 고정.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | `POST /api/jobs` + `Idempotency-Key: {key}` | `201 {job:J}` |
| 2 | 동일 키로 `POST /api/jobs` 재시도 (payload 동일) | `200 {job:J}` — id 동일 |
| 3 | 동일 키 + **다른 payload** | `409 {error:{code:"IDEMPOTENCY_CONFLICT", message:"payload mismatch for same idempotency_key"}}` |
| 4 | 사용자 B 로 동일 키 사용 | `201` — UNIQUE 가 `(user_id, key)` 복합 |
| 5 | 동시 요청 2건 병렬 발사 (Promise.all 동일 키 동일 payload) | 정확히 1건 `201`, 나머지 1건 `200` 또는 `409 IDEMPOTENCY_CONFLICT`. **둘 다 5xx 아님** |
| 6 | 다른 사용자 B 의 Job 을 사용자 A 가 `GET /api/jobs/{B-job-id}` | `404` (IDOR 차단, 존재 자체 비공개). 보안 audit 시나리오와 중복 검증 |

**실패 분류.** 1·2 미통과 = P0. 3·4·5 미통과 = P1. 5 에서 5xx 발생 = **CRITICAL** (Redis 락 누수).

---

## 시나리오 7 — SSE 끊김 → 자동 재연결 + Last-Event-ID 백필 (P0)

**검증 포인트.** 60초 이내 끊김 동안 발행된 이벤트가 재연결 후 `Last-Event-ID` 기반 백필로 **누락 없이 도착**. Redis Stream `events:jobs:user:<uid>:stream` 이 SSOT. 백필 후 실시간 pub/sub 전환.

### Given
- 사용자 A 로그인. recorder 가 `/api/events/jobs` 구독.
- 워커 동시성 1.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | 작업 A1 제출 (`seconds:2`) → recorder.untilEvent(`job.succeeded`) | 이벤트 1세트 정상 수신. `lastEventId` 기억 |
| 2 | recorder.disconnect() — TCP close 시뮬레이션 | EventSource readyState != OPEN |
| 3 | 끊긴 상태에서 작업 A2 제출 (`seconds:2`) — 서버는 publish + XADD 모두 수행 | API 에는 `201`. SSE 클라이언트는 아직 수신 못 함 |
| 4 | 30s 이내 작업 A3 제출 (`seconds:2`) | A3 도 stream 에 누적 |
| 5 | recorder.reconnect() — 표준 EventSource 가 `Last-Event-ID: <step1 lastEventId>` 자동 송신 | 서버는 stream 에서 백필 → SSE 로 푸시 |
| 6 | recorder 가 백필 + 실시간 모두 수신 후 untilEvent(`job.succeeded`) ×2 | A2·A3 의 `submitted`/`started`/`succeeded` 모두 도착, **id 단조증가**, 누락 0건 |
| 7 | 재연결 직후 첫 이벤트의 `id:` 가 step1 의 `lastEventId` 보다 큰 ULID | 단조성 보장 |
| 8 | 60초 분량 초과로 stream 이 잘렸을 때 (회귀 케이스, regression.md 로 이동) | 서버가 `event: catchup_overflow` 발행 후 클라이언트 풀 리프레시 유도 |

**실패 분류.** 6 의 누락 발생 = P0. 7 의 단조성 위반 = P0 (백필 정합성). 백필 중 500 = **CRITICAL**.

**구현 메모 (마크).** SSE recorder 의 `disconnect()` 는 underlying TCP 를 강제 close. EventSource 의 표준 재연결을 그대로 활용. 서버는 `Last-Event-ID` 헤더가 있으면 stream 의 해당 ID 이후를 XRANGE 로 100건 또는 60s 분량 백필 후 pub/sub 전환.

---

## 시나리오 8 — 멀티 인스턴스 sampler 단일 리더 (P1)

**검증 포인트.** 두 API 인스턴스 동시 가동 시 `queue.counts` 와 `queue.workers` 가 중복 발행되지 않음. `heartbeat:queue_emitter` Redis 키 (`SET NX EX 10`) 가 단일 리더 보장. 리더 종료 시 다른 인스턴스가 10초 내 승계.

### Given
- API 인스턴스 2개 (`api-A`, `api-B`) 동시 가동. 동일 Redis/PG/Celery.
- 사용자 A 로그인. recorder 가 `api-A` 의 `/api/events/jobs` 구독.

### When / Then

| Step | When | Then |
|---|---|---|
| 1 | 10초 동안 recorder 가 `queue.counts` 이벤트 수신 | `queue.counts` 가 **정확히 1초당 1건** ±debounce (동일값 skip) 패턴으로 도착. 2건/sec 같은 중복 없음 |
| 2 | `queue.workers` 동일 검증 | **5초당 1건** ±jitter 도착. 중복 없음 |
| 3 | Redis 에서 `GET heartbeat:queue_emitter` 직접 조회 | 값이 `api-A` 또는 `api-B` 중 하나, TTL ≤ 10s |
| 4 | 리더 인스턴스 종료 (`docker kill api-A` 가정) | 10초 이내 `api-B` 가 락 획득. recorder 는 `api-A` 가 죽었으므로 재로그인하여 `api-B` SSE 구독 |
| 5 | step 4 이후 10초 관측 | `queue.counts` 가 다시 정상 빈도로 도착 (잠시 끊겼다가 재개) |
| 6 | 두 인스턴스가 동시에 `queue.counts` 를 publish 한 흔적 검출 | Redis MONITOR 로 1초 윈도우에 두 인스턴스 PID 가 동일 채널에 publish 한 사례가 **없어야 함** |

**실패 분류.** 1·2 의 중복 발행 = P1 (대시보드 잡음, ACK 비용). 6 의 중복 publish = **CRITICAL** (락 메커니즘 무력화). 4 이후 30초가 지나도 emitter 가 살아나지 않음 = P0.

**환경 메모.** 본 시나리오는 정식 E2E 가 아니라 **회귀 환경 변형**으로 분류해도 충분. Playwright 단독으로는 두 인스턴스 직접 띄우기 부담스러우므로 마크가 `docker compose -f compose.multi.yml up` 헬퍼를 제공하고, 정민이 PR 별이 아닌 **주간 회귀 batch** 로 운영. (regression.md 7번 참조.)

---

## 사전 합의 사항

### CTO 답변 확정 (2026-05-19, [inspection-T5-jungmin.md](inspection-T5-jungmin.md))

- ~~**Q-A3.** retry 시 Idempotency-Key 누락 정책.~~ → **허용** (ADR §3.3). 시나리오 5 step 8·9 로 양 경로 검증. ✅ 반영 완료.

### 마크 회신 필요 (자동화 직전)

- **Q-A1.** 시나리오 1 의 `SESSION_ABS_TTL_OVERRIDE_SEC` 환경변수 수용 가능 여부. 거절 시 Redis CLI 헬퍼로 sid TTL 만료 시뮬레이션.
- **Q-A2.** 시나리오 3 의 `CELERY_BACKOFF_BASE_SEC=0.1` 수용 가능 여부. 거절 시 시나리오 전체 실행 시간 60s+ 로 증가하나 정확성 우선.
- **Q-A4.** 시나리오 8 의 멀티 인스턴스 dev 환경 셋업 (compose.multi.yml) — 첫 PR 에 포함할지 별도 PR 로 뺄지.

회신은 `team-send 정민 "[T5] Q-A1/2/4: ..."` 로. (제임스가 마크에 별도 위임 완료.)

### 외부 의존

- **ADR-001 Patch 3 (네이선)** — `succeeded` retry 불가 명시 (§3.3 또는 §4.3 한 줄). 반영 전까지 시나리오 5 step 10 은 자동화 enabled 상태로 둘 수 있으나, ADR 미반영 상태에서 실패 시 P2 로 분류 (스펙 불일치 한정). Patch 3 머지 후 HIGH 로 격상.

---

## 자동화 인덱스

| 시나리오 | 자동화 위치 | 자동화 코드 작성 | 시나리오 정의·리뷰 |
|---|---|---|---|
| 1 | `tests/e2e/auth.spec.ts` | 마크 | 정민 |
| 2 | `tests/e2e/job-happy-path.spec.ts` | 마크 | 정민 |
| 3 | `tests/e2e/job-retry-failed.spec.ts` | 마크 | 정민 |
| 4 | `tests/e2e/job-cancel.spec.ts` | 마크 | 정민 |
| 5 | `tests/e2e/job-retry-patch.spec.ts` | 마크 | 정민 |
| 6 | `tests/e2e/idempotency.spec.ts` | 마크 | 정민 |
| 7 | `tests/e2e/sse-reconnect.spec.ts` | 마크 | 정민 |
| 8 | `tests/e2e/multi-instance-leader.spec.ts` (회귀 batch) | 마크 | 정민 |

## 운영 규칙

- 시나리오 추가·변경은 본 문서 PR 로만. 본문에 변경자·일자·사유 패치 노트 추가.
- 각 PR 의 머지 게이트 ([review-log.md](review-log.md)) 는 해당 PR 영향 범위의 시나리오만 실행 (스모크). 전체 8건은 `develop/<product>/<version>` → `main` 머지 PR 에서만 1회 풀.
- flaky 시나리오는 1회 자동 retry 허용. 2회 연속 실패 시 차단 + 정민이 원인 분석 코멘트.
