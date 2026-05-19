# ADR-001: 실시간 작업 큐 대시보드 — 시스템 아키텍처

- 상태: **Accepted**
- 일자: 2026-05-19
- 작성자: 네이선 (Architect)
- 의사결정자: 제임스 (CTO), 네이선 (Architect)
- 상위 결정: [2026-05-19-realtime-task-queue-dashboard.md](2026-05-19-realtime-task-queue-dashboard.md)
- 대응 태스크: T1
- 범위: 시범 프로젝트 1차 골격. 분산·멀티리전·결제 미포함.

## 0. 요약 (TL;DR)

| 영역 | 결정 |
|---|---|
| 실시간 채널 | **SSE 2채널** — `/api/events/jobs` (사용자+시스템) / `/api/events/jobs/:id` (작업 상세 고빈도). 양방향 명령은 REST PATCH |
| 이벤트 팬아웃 | **Redis pub/sub 3채널** — `events:jobs:user:<uid>` · `events:jobs:job:<jid>` · `events:system:queue` |
| Redis 버전·보안 | **7.4.2 이상** 고정 (RediShell CVE-2025-49844 픽스), requirepass·바인딩·FLUSHALL/CONFIG 비활성화 — R-006 |
| 큐 모델 | Celery 우선순위 큐 2종 (`high`, `default`). 라우팅 키 = 작업 타입 |
| 재시도 | 지수 백오프 1s→4s→16s, 최대 3회. `idempotency_key` 로 중복 방어 |
| 데이터 모델 | `users` / `jobs` / `job_events` 3 테이블 + Redis 세션·pub/sub |
| 작업 상태 | `pending → running → succeeded | failed | canceled` |
| 인증 | 세션 쿠키(`sid`) + Redis 저장, httpOnly·Secure·SameSite=Lax, TTL 14d |
| CSRF | 상태 변경 요청에 한해 double-submit 토큰 |
| 관측성 | 구조화 JSON 로그 + Prometheus `/metrics` + `X-Request-Id` 트레이스 |
| 인터페이스 변경 절차 | §4·§5·§6 변경 PR 은 **네이선 승인 필수**, 별도 ADR 발행 |

---

## 1. 시스템 컨텍스트

### 1.1 컴포넌트 다이어그램 (C4 Level 2)

```
                       ┌──────────────────────────────┐
                       │  Browser (React + Vite + TS) │
                       │   - 대시보드 UI               │
                       │   - SSE 클라이언트            │
                       │   - fetch + CSRF 토큰         │
                       └────────┬───────────┬─────────┘
                                │ HTTPS     │ HTTPS (SSE: text/event-stream)
                                ▼           ▼
                       ┌──────────────────────────────┐
                       │  Flask API (gunicorn x N)    │
                       │  - /auth, /api/jobs          │
                       │  - /api/events/jobs (SSE)    │
                       │  - /metrics                  │
                       └──┬──────────┬─────────┬──────┘
              세션·pub/sub │   ORM    │         │ Celery 작업 enqueue
                          ▼          ▼         ▼
                   ┌───────────┐ ┌────────┐ ┌───────────────┐
                   │  Redis    │ │  PG    │ │  Celery Broker│
                   │  - sid:*  │ │ users  │ │  (Redis 동일) │
                   │  - events │ │ jobs   │ └──────┬────────┘
                   │   pub/sub │ │ events │        │
                   └─────▲─────┘ └────▲───┘        ▼
                         │            │     ┌────────────────┐
                         │ events 발행 │ ORM │ Celery Worker  │
                         └────────────┴─────┤ (N 프로세스)    │
                                            └────────────────┘
```

### 1.2 데이터 흐름

1. **작업 제출**: 브라우저 → API `POST /api/jobs` → PG `jobs INSERT(pending)` → Celery enqueue → `job_events(submitted)` 기록 → Redis 채널 publish.
2. **작업 실행**: 워커가 작업 수신 → `jobs UPDATE(running)` + `job_events(started)` → 작업 본문 실행 → `succeeded|failed` 로 종결 + 이벤트 기록.
3. **실시간 푸시 (사용자 채널)**: SSE 핸들러가 `events:jobs:user:<uid>` + `events:system:queue` 를 다중 SUBSCRIBE → 한 SSE 연결로 작업·시스템 이벤트 전달.
4. **실시간 푸시 (작업 상세)**: 사용자가 작업 상세를 열면 `/api/events/jobs/:id` 가 `events:jobs:job:<jid>` 를 구독 → `progress`/`log_line` 고빈도 스트림 전용.
5. **시스템 sampler**: 단일 리더 API 인스턴스(`heartbeat:queue_emitter` 락 보유) 가 1s/5s 주기로 `queue.counts`/`queue.workers` 를 시스템 채널에 publish.
6. **양방향 명령**: 취소·재시도는 `PATCH /api/jobs/:id` (HTTP 요청). 워커가 상태 전환 시 다음 이벤트로 통지.
7. **테스트 빌드 한정 측정 훅**: `ENABLE_EMIT_AT=true` 인 워커는 publish 직전 페이로드에 `_emit_at` 부착 → 테스트 클라이언트(`X-Perf-Client: test`) 만 응답에서 수신 → `sse_emit_to_receive_seconds` 히스토그램 관측 (§5.4.3, §7.2).

### 1.3 배포 가정 (시범)

- 단일 환경 단일 인스턴스(API·Celery·Redis·PG 각 1). R-004 (Redis SPOF) 는 시범에서 수용.
- 수직 스케일 우선. API 는 gunicorn worker 2 ~ 4 로 시작.

---

## 2. 실시간 통신 결정 — SSE 1차 채택

### 2.1 옵션 비교 (재검증)

| 옵션 | 구현 비용 | 운영 비용 | 양방향 | Celery 친화 | p95 < 500ms 충족 | 결론 |
|---|---|---|---|---|---|---|
| A. **SSE** | 저 | 저 | ✗ (단방향) | ✅ Redis pub/sub 와 자연 매칭 | ✅ | **채택** |
| B. WebSocket | 중 | 중 | ✅ | ✅ | ✅ | 거절 — 양방향 필요성 낮음, 프록시/HTTP/2 친화도 SSE 가 우위 |
| C. 폴링 (3 ~ 5s) | 저 | 중 | ✗ | ✅ | ⚠️ 지연·서버 부하 | 거절 — 평가 4축 중 성능 충족 어려움 |

### 2.2 채택 근거

- 작업 큐 도메인은 본질적으로 **서버 → 클라이언트 푸시** 패턴. 양방향 RPC 가 거의 없다.
- 양방향 필요 명령(취소·재시도) 은 **REST PATCH** 로 분리해도 UX 영향이 없다(낮은 빈도, 사용자 인지 지연 허용).
- HTTP/1.1·HTTP/2 · 프록시·로드밸런서 호환 — WebSocket 보다 운영 단순.
- Celery 결과를 Redis pub/sub 로 발행 → API 가 SSE 로 중계 → **자연스러운 fanout**.

### 2.3 양방향 명령 처리 경로

| 시나리오 | 경로 |
|---|---|
| 작업 취소 | `PATCH /api/jobs/:id {status:"canceled"}` → API 가 PG 갱신 + Celery revoke + `job_events(canceled)` publish |
| 작업 재시도 | `PATCH /api/jobs/:id {action:"retry"}` → 새 `jobs` 행 생성 + 이전 행에 `retried_to_job_id` 기록 |
| 우선순위 변경 | M1 범위 외 (보류) |

### 2.4 끊김·재연결 정책

- 클라이언트는 표준 `EventSource` 사용 — 끊김 시 자동 재연결 (브라우저 기본 ~3s).
- 서버는 모든 이벤트에 `id:` 필드를 ULID 로 부여.
- 재연결 시 클라이언트는 `Last-Event-ID` 헤더를 자동 송신.
- 서버는 `Last-Event-ID` 가 있으면 **Redis Stream 백필** 에서 해당 ID 이후 이벤트를 최대 100건 또는 60초 분량 재전송한 뒤, 실시간 pub/sub 로 전환.
  - Redis Stream 키: `events:jobs:user:<user_id>:stream`. 30분 TTL (XADD + MAXLEN ≈ 1000).
- keep-alive 주석 (`: ping\n\n`) 을 15초마다 전송.
- 서버는 1시간 단위로 클라이언트를 정중 종료 (`event: bye`) → 자동 재연결 사이클.

### 2.5 멀티 워커·멀티 API 환경의 팬아웃

- 워커는 항상 **Redis 에 publish** + **Redis Stream 에 XADD** 둘 다 수행 (XADD 가 SSOT, publish 는 저지연 fanout).
- API 인스턴스는 같은 Redis 에서 SUBSCRIBE 하므로, 어느 API 노드에 접속한 클라이언트라도 동일 이벤트를 받는다.
- 동일 사용자가 여러 탭을 띄워도 각 EventSource 가 같은 채널을 구독하므로 자연 fanout.

### 2.6 거절된 대안

- **WebSocket** — 시범에서 양방향 필요성 부재. 운영 복잡도 증가.
- **롱폴링** — SSE 와 같은 단방향이면서 구현 단순성·재연결 의미론에서 SSE 가 우위.
- **클라이언트 직접 Redis 구독** — 보안·인증 위반. 거절.

---

## 3. 큐 모델

### 3.1 큐 구성

| Celery Queue | 우선순위 | 작업 유형 | 비고 |
|---|---|---|---|
| `high` | 높음 | 사용자 즉시 응답 필요한 작업 | M1 미사용, 인터페이스만 확보 |
| `default` | 보통 | 일반 더미 작업 (5 ~ 30s 시뮬레이션 + 실패 케이스) | 시범 주요 트래픽 |

- 큐 우선순위는 **Celery worker 의 큐 구독 순서** 로 구현 (`-Q high,default`). Redis 자체 priority 키 사용 안 함 (운영 단순화).
- 라우팅: `task_routes` 매핑 — 작업 타입 → 큐. 신규 작업 타입 추가는 ADR 수정 사항이 아닌 코드 변경.

### 3.2 재시도·백오프

자동 재시도(워커 내부) 와 사용자 수동 재시도(REST PATCH) 는 **분리**된 메커니즘이다.

#### 자동 재시도 (Celery)

- Celery `autoretry_for=(TransientError,)`, `retry_backoff=True`, `retry_backoff_max=60`, `max_retries=3`.
- 효과: 1s → 4s → 16s (jitter 포함), 그 후 `failed` 확정.
- `PermanentError` (검증 실패 등) 는 재시도 없이 즉시 `failed`.

#### 수동 재시도 (`PATCH /api/jobs/:id {action:"retry"}`)

- **허용 상태**: `failed` 또는 `canceled` 만 (§4.3 상태 머신 참조).
- **거부 상태**: `pending`/`running` (의미 없음 — 이미 진행 중), `succeeded` (의미적 정합 — 성공 결과 재실행은 별개 도메인).
- 거부 시 응답: `409 CONFLICT` + `{error:{code:"INVALID_TRANSITION", message:"retry not allowed from <status>"}}`.
- 성공 시: 새 `jobs` 행 생성, 원본 행의 `retried_to_job_id` 갱신, `job.retried` 이벤트 발행.
- **`succeeded` 의 재실행 시나리오**는 별도 `clone` 액션으로 후속 ADR 에서 분리 (M1 범위 외). 출처: `docs/qa/scenarios.md SM-4`.

### 3.3 Idempotency Key

- `POST /api/jobs` 요청 시 클라이언트가 `Idempotency-Key: <ulid>` 헤더 송신.
- API 는 `jobs.idempotency_key` (unique per user) 로 중복 제출 차단 → 동일 키 재요청은 기존 `jobs` 행을 200 으로 반환.
- 누락 시 서버가 ULID 생성하여 응답에 포함 (클라이언트가 재시도 시 사용).

### 3.4 실패 격리

- 워커는 작업당 try/except 로 감싸 예외 → `failed` 상태 + `job_events(failed, error=<msg>)`. 워커 프로세스는 죽지 않는다.
- 워커 OOM·crash 시 Celery 의 `acks_late=True` + `task_reject_on_worker_lost=True` 로 한 번 자동 재큐.

---

## 4. 데이터 모델

### 4.1 PostgreSQL

```sql
-- users : 인증 주체
CREATE TABLE users (
  id              UUID PRIMARY KEY,
  email           TEXT NOT NULL UNIQUE,
  password_hash   TEXT NOT NULL,            -- argon2id
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- jobs : 큐에 올라간 작업 단위
CREATE TABLE jobs (
  id                 UUID PRIMARY KEY,
  user_id            UUID NOT NULL REFERENCES users(id),
  type               TEXT NOT NULL,         -- 예: "dummy.sleep"
  payload            JSONB NOT NULL DEFAULT '{}'::jsonb,
  priority           SMALLINT NOT NULL DEFAULT 0,  -- 0=default, 10=high
  status             TEXT NOT NULL          -- 'pending'|'running'|'succeeded'|'failed'|'canceled'
                       CHECK (status IN ('pending','running','succeeded','failed','canceled')),
  attempts           SMALLINT NOT NULL DEFAULT 0,
  idempotency_key    TEXT NOT NULL,
  celery_task_id     TEXT,                  -- Celery 측 식별자 (취소·조회용)
  error              TEXT,                  -- 실패 시 메시지 (sanitized)
  retried_to_job_id  UUID REFERENCES jobs(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at         TIMESTAMPTZ,
  finished_at        TIMESTAMPTZ,
  UNIQUE (user_id, idempotency_key)
);
CREATE INDEX idx_jobs_user_created  ON jobs (user_id, created_at DESC);
CREATE INDEX idx_jobs_status        ON jobs (status) WHERE status IN ('pending','running');

-- job_events : 작업 단위 이벤트 로그 (SSE 의 소스)
CREATE TABLE job_events (
  id          BIGSERIAL PRIMARY KEY,
  job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id),  -- denorm, fanout 키
  type        TEXT NOT NULL,                -- 'submitted'|'started'|'progress'|'succeeded'|'failed'|'canceled'|'retried'
  payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
  event_ulid  TEXT NOT NULL UNIQUE,         -- SSE id: 와 동일 값
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_job_events_user_created ON job_events (user_id, created_at DESC);
CREATE INDEX idx_job_events_job_created  ON job_events (job_id, created_at);
```

### 4.2 Redis (비관계)

> **버전·보안 SSOT (R-006)** — Redis 서버 버전은 **7.4.2 이상** 으로 고정 (CVE-2025-49844 RediShell CVSS 10.0, CVE-2024-46981 픽스 포함). 인증(`requirepass`), 바인딩(`127.0.0.1` 또는 사설망 한정), 위험 명령(`FLUSHALL`/`CONFIG`) `rename-command ""` 으로 비활성화 필수. 마크의 `docker-compose.yml` 과 본 ADR §4.2 가 양쪽 SSOT — 변경은 §8 절차로만. 출처: `docs/analysis/dependency-audit.md §3`.

| 키 | 용도 | TTL |
|---|---|---|
| `sid:<ulid>` (Hash) | 세션 본문 `{user_id, ua, ip, created_at}` | 14d (활동 시 슬라이딩 갱신) |
| `user_sids:<user_id>` (Set) | 사용자별 활성 세션 ID — `revokeAllFor` 용 | 세션 만료 시 정리 |
| `events:jobs:user:<user_id>` (pub/sub) | 사용자 작업 이벤트 fanout 채널 | — |
| `events:jobs:user:<user_id>:stream` (Stream) | 사용자 채널 이벤트 백필 (Last-Event-ID 재연결) | MAXLEN≈1000, 30분 |
| `events:jobs:job:<job_id>` (pub/sub) | 작업 상세 채널 fanout (`progress`,`log_line`) | — |
| `events:jobs:job:<job_id>:stream` (Stream) | 작업 상세 채널 백필 | MAXLEN≈2000, 15분 |
| `events:system:queue` (pub/sub) | 시스템 전역 sampler 채널 (`queue.counts`,`queue.workers`) | — |
| `heartbeat:queue_emitter` (String) | sampler 단일 리더 락 (`SET NX EX 10`) | 10s |
| `csrf:<sid>` | CSRF 토큰 (double-submit) | 세션과 동일 |
| `idem:<user_id>:<key>` | 짧은 in-flight 중복 락 (PG UNIQUE 백업) | 60s |

### 4.3 상태 머신

```
        ┌────────────────────┐
        │                    │  (취소)
        ▼                    │
   ┌─────────┐    enqueue   ┌────────┐
   │ pending │──────────────│canceled│
   └────┬────┘              └────────┘
        │ worker pick
        ▼
   ┌─────────┐    error / retry exhausted
   │ running │──────────────┐
   └────┬────┘              │
        │                   ▼
        │ ok           ┌────────┐
        ▼              │ failed │
   ┌──────────┐        └────────┘
   │succeeded │
   └──────────┘
```

- 모든 전환은 단방향. `succeeded` / `failed` / `canceled` 는 종결 상태.
- `pending` → `canceled` 는 워커 pick 전, `running` → `canceled` 는 Celery revoke + 워커 측 SIGUSR 협조로 best-effort (작업이 이미 끝났으면 `succeeded`/`failed` 우선).
- **종결 상태에서의 사용자 액션** (수동 retry 정책 — §3.2 참조):

| 종결 상태 | `PATCH retry` | 비고 |
|---|---|---|
| `failed` | 허용 — 새 `jobs` 행 생성 (원본 행 불변, `retried_to_job_id` 링크) | M1 범위 |
| `canceled` | 허용 — 동일 | M1 범위 |
| `succeeded` | **거부** (`409 INVALID_TRANSITION`) | 성공 결과 재실행은 의미적으로 다른 액션. 후속 ADR 의 `clone` 액션으로 분리(M1 외) |

---

## 5. API 인터페이스 — 1차

### 5.1 엔드포인트

| METHOD | PATH | 요청 | 응답 | 인증 | 비고 |
|---|---|---|---|---|---|
| POST | `/auth/login` | `{email, password}` | `204` + `Set-Cookie: sid=...` | — | 5 req/min/IP |
| DELETE | `/auth/session` | — | `204` | 세션 | 현재 세션 로그아웃 |
| DELETE | `/auth/sessions` | — | `204` | 세션 | 전체 디바이스 로그아웃 (revokeAllFor) |
| GET | `/api/me` | — | `{userId, email}` | 세션 | 초기 부트스트랩 |
| POST | `/api/jobs` | `{type, payload?, priority?}` + `Idempotency-Key` | `201 {job}` | 세션 + CSRF | 작업 제출 |
| GET | `/api/jobs` | `?status=&limit=&cursor=` | `{items:[job], nextCursor}` | 세션 | 페이지네이션, default limit 50 |
| GET | `/api/jobs/:id` | — | `{job, recentEvents:[event]}` | 세션 | recentEvents 최대 50 |
| PATCH | `/api/jobs/:id` | `{status:"canceled"} \| {action:"retry"}` | `200 {job}` | 세션 + CSRF | 양방향 명령. `retry` 는 `failed`/`canceled` 만 허용(§3.2/§4.3), `succeeded` 는 `409 INVALID_TRANSITION` |
| GET | `/api/events/jobs` | (Last-Event-ID 헤더) | `text/event-stream` | 세션 | SSE 채널 — 사용자 작업 이벤트 + 시스템 큐 fanout |
| GET | `/api/events/jobs/:id` | (Last-Event-ID 헤더) | `text/event-stream` | 세션 + 소유자 검증 | SSE 채널 — 작업 상세 고빈도(`progress`,`log_line`) 전용 |
| GET | `/healthz` | — | `200 {ok:true, deps:{...}}` | — | LB 헬스체크 |
| GET | `/metrics` | — | Prometheus text | 내부망 한정 | 카맥 perf 게이트 |

### 5.2 `job` 객체 표준 형태 (응답 공통)

```json
{
  "id": "01J...",
  "type": "dummy.sleep",
  "status": "running",
  "priority": 0,
  "attempts": 1,
  "payload": { "seconds": 12 },
  "error": null,
  "createdAt": "2026-05-19T13:30:00Z",
  "startedAt": "2026-05-19T13:30:01Z",
  "finishedAt": null
}
```

### 5.3 SSE 채널

대시보드는 **두 종류의 SSE 채널** 을 사용한다.

#### 5.3.1 사용자 채널 — `GET /api/events/jobs`

- Content-Type: `text/event-stream; charset=utf-8`, Cache-Control: `no-cache`.
- 연결당 사용자 1명. 사용자 식별은 세션 쿠키.
- **다중 SUBSCRIBE**: API 핸들러가 두 Redis 채널을 동시에 구독해 같은 SSE 연결로 전달.
  - `events:jobs:user:<user_id>` — 작업 단위 이벤트 (`job.*`)
  - `events:system:queue` — 시스템 전역 이벤트 (`queue.counts`, `queue.workers`)
- 사용자 채널의 `job.progress` 는 **1s throttle** (대시보드 카드용 저빈도).
- 이벤트 형식:

```
id: 01J5KZS0WBA2H6CKDXYZ
event: job.started
data: {"jobId":"01J...","startedAt":"2026-05-19T13:30:01Z","attempts":1}

id: 01J5KZS0WBA2H6CKDABC
event: queue.counts
data: {"pending":12,"running":4,"succeeded":128,"failed":3,"at":"..."}
```

#### 5.3.2 작업 상세 채널 — `GET /api/events/jobs/:id`

- 작업 상세 화면 전용. **고빈도 `progress` + 대용량 `log_line`** 을 전체 사용자 채널에 흘리지 않기 위한 분리.
- 소유자 검증: 세션 사용자의 `jobs.user_id` 와 일치해야 함. 불일치 시 `403 FORBIDDEN`.
- 라이프사이클: 작업 상세 모달/페이지가 열린 동안만 구독. 종결 상태(`succeeded|failed|canceled`) 이벤트 수신 후 60초 뒤 서버가 정중 종료(`event: bye`).
- `progress` 는 raw 전송(throttle 없음), `log_line` 은 작업 표준출력 라인 단위.
- Redis 채널: `events:jobs:job:<job_id>` (pub/sub) + `events:jobs:job:<job_id>:stream` (백필, MAXLEN≈2000, TTL 15분).
- 이벤트 형식:

```
id: 01J...
event: job.progress
data: {"jobId":"01J...","progress":0.42,"at":"..."}

id: 01J...
event: log_line
data: {"jobId":"01J...","line":"step 3/8 done","at":"..."}
```

### 5.4 이벤트 타입 카탈로그

채널 표기: `U` = 사용자 채널 `/api/events/jobs`, `D` = 작업 상세 채널 `/api/events/jobs/:id`.

| event | 채널 | data 형태 | 발행 시점 | 빈도/정책 |
|---|---|---|---|---|
| `job.submitted` | U | `{jobId, type, priority, createdAt}` | API enqueue 직후 | 작업당 1회 |
| `job.started` | U | `{jobId, startedAt, attempts}` | 워커 pick 직후 | 작업당 N (재시도 포함) |
| `job.progress` | U, D | `{jobId, progress: 0..1, at}` | 워커가 명시적으로 보고 시 | U: 작업당 **1s throttle**, D: raw |
| `job.succeeded` | U | `{jobId, finishedAt, result?}` | 정상 종료 | 작업당 1회 |
| `job.failed` | U | `{jobId, finishedAt, error}` | 재시도 소진 또는 영구 실패 | 작업당 1회 |
| `job.canceled` | U | `{jobId, finishedAt}` | 취소 확정 | 작업당 1회 |
| `job.retried` | U | `{jobId, newJobId}` | 재시도 신규 행 생성 | 재시도당 1회 |
| `queue.counts` | U | `{pending, running, succeeded, failed, at}` | counts emitter sampler | **1s throttle/debounce** — 직전 publish 와 동일 값이면 skip |
| `queue.workers` | U | `{active, total, throughput, at}` | workers emitter sampler | **5s 주기** (정기) |
| `log_line` | D | `{jobId, line, at}` | 워커의 작업 stdout 라인 단위 | 라인당 1회, max 200 bytes/line |

#### 5.4.1 시스템 sampler — `queue.counts` / `queue.workers`

- 단일 리더로 동작. **`heartbeat:queue_emitter`** Redis 키에 `SET NX EX 10` 으로 락을 잡은 API 인스턴스 한 곳만 emitter 가 됨. 락 만료 시 다른 인스턴스가 승계.
- `queue.counts` — PG `jobs` 의 status 별 카운트를 1초 주기 sample. 마지막 publish 와 동일하면 skip (debounce). 디스플레이 부하 및 ACK 비용 절감.
- `queue.workers` — Celery `inspect().active()` / `stats()` 를 5초 주기 sample. `active` = 현재 실행 중 작업 수, `total` = 가동 워커 수, `throughput` = 직전 60초 succeeded+failed 합 ÷ 60.
- 두 이벤트는 **시스템 전역 채널** `events:system:queue` 로 publish. 모든 사용자가 동일 값을 본다(시스템 정보).

#### 5.4.2 `log_line` 분리 근거

- 단일 작업이 분당 수백 라인을 출력할 수 있는 고빈도 스트림. 사용자 채널에 흘리면 다른 클라이언트의 SSE 버퍼를 차지하여 큐/카드 갱신 지연을 유발.
- 사용자가 작업 상세를 열 때만 구독 → 트래픽 라이프사이클이 화면 라이프사이클과 일치.
- 워커는 항상 `events:jobs:job:<job_id>:stream` 에 XADD (백필 가능). 작업 상세 화면이 열려 있지 않으면 pub/sub 수신자는 없지만 Stream 에는 누적되어, 화면 진입 시 `Last-Event-ID` 가 없으면 직전 200건을 1회 백필 후 실시간 전환.

#### 5.4.3 테스트 빌드 한정 측정 훅 — `_emit_at`

SSE push-to-receive 지연 측정용 페이로드 필드. 카맥 perf 측정과 ADR-001 §7.2 신규 히스토그램의 데이터 소스. 출처: `docs/performance/baseline.md §4.1`, `docs/qa/inspection-T6-carmack.md`.

- **필드명**: `payload._emit_at` — `_` prefix 는 운영 응답 직렬화 시 strip 대상 표식.
- **부착 위치**: 워커가 `events:jobs:user:<uid>` · `events:jobs:job:<jid>` · `events:system:queue` 어느 채널로 publish 하든 직전에 부착.
- **포맷**: 두 형식 동시 기록 — `{ "_emit_at": { "iso": "2026-05-19T13:30:01.123456Z", "monotonic_ns": 17321840123456789 } }`. `iso` 는 사람·로그 가독·NTP 동기 환경의 차이 계산용, `monotonic_ns` 는 동일 머신 내 단조 시계 차이 검증용(클라가 동일 컨테이너/머신일 때만 의미).
- **계산식**: `push_to_receive_ms = (receive_at - _emit_at.iso) × 1000`. 카맥 `load_tests/locustfile_sse_latency.py` 가 이 식으로 측정 후 `sse_emit_to_receive_seconds` 히스토그램 관측.

##### 운영 노출 금지 — 다층 가드

부착(워커) ↔ 노출(API 응답) 은 **AND 조건** 으로 분리해 단일 실수로 누출되지 않도록 한다.

| 층 | 가드 | 누락 시 결과 |
|---|---|---|
| 워커 부착 | `ENABLE_EMIT_AT=true` 일 때만 페이로드에 부착. 미설정·`false`·임의 값은 모두 비활성 | 페이로드 자체에 필드 없음 |
| 운영 빌드 | 운영 컴포즈·배포 매니페스트는 이 변수를 **설정하지 않음**. CI 빌드 게이트에서 운영 이미지에 변수 누락 검증 | 운영 워커는 항상 비활성 |
| API 직렬화 | SSE 핸들러는 페이로드 직렬화 직전 `_` prefix 키를 **무조건 제거**. 테스트 빌드에서만 strip 우회 | 환경 변수가 잘못 켜져도 클라로 안 새어나감 |
| 클라이언트 식별 | 테스트 클라이언트는 `X-Perf-Client: test` 헤더 송신. 헤더 미존재 시 strip 적용 (환경 변수 무관) | 일반 브라우저 트래픽은 항상 strip |
| 로그 | `_emit_at` 페이로드는 §7.1 구조화 로그 필드에 출력 금지 | 로그 사이드채널 방지 |

노출 조건: `ENABLE_EMIT_AT=true` **∧** `X-Perf-Client: test` 헤더 존재 — 둘 다 만족해야만 직렬화 응답에 살아남는다.

##### 보안 근거

운영 사용자에게 `_emit_at` 가 노출되면 워커 처리 시각·서버 단조 시계가 측면 채널로 새어 IDOR/타이밍 오라클(예: 작업 ID 추측, 사용자별 처리 비용 추론) 로 악용될 수 있다 — §OWASP 표의 A01·A09 갱신.

##### 마크 구현 분기 (요약)

```python
# 워커 publish 직전 (worker/celery_app.py 등)
if os.getenv("ENABLE_EMIT_AT") == "true":
    payload["_emit_at"] = {
        "iso": datetime.now(timezone.utc).isoformat(),
        "monotonic_ns": time.monotonic_ns(),
    }

# API SSE 직렬화 직전 (api/sse.py 등)
def _strip_underscore_keys(d):
    return {k: v for k, v in d.items() if not k.startswith("_")}

allow_emit = (
    os.getenv("ENABLE_EMIT_AT") == "true"
    and request.headers.get("X-Perf-Client") == "test"
)
serialized_payload = payload if allow_emit else _strip_underscore_keys(payload)
```

- 부착/strip 분기가 두 모듈에 흩어지지 않도록 헬퍼(`utils/emit_timing.py`) 로 추출 권장.
- 단위 테스트: 환경 변수 ON + 헤더 부재 → strip 적용 검증, 환경 변수 OFF + 헤더 존재 → 페이로드에 필드 부존재 검증.

### 5.5 오류 응답 표준

```json
{ "error": { "code": "VALIDATION_FAILED", "message": "type is required", "details": {...} } }
```

`code` 카탈로그: `UNAUTHENTICATED`, `FORBIDDEN`, `CSRF_FAILED`, `VALIDATION_FAILED`, `RATE_LIMITED`, `IDEMPOTENCY_CONFLICT`, `INVALID_TRANSITION`, `NOT_FOUND`, `INTERNAL`.

---

## 6. 인증·세션

### 6.1 결정

- **세션 + Redis 저장** 채택 (상위 결정 메모와 일치).
- 비밀번호 해시: **argon2id** (memory=64MB, iterations=3, parallelism=1).
- 세션 ID: 128-bit 무작위 ULID, 쿠키명 `sid`.

### 6.2 쿠키 정책

| 속성 | 값 |
|---|---|
| `HttpOnly` | true |
| `Secure` | true (운영) / false (로컬 dev) |
| `SameSite` | `Lax` |
| `Path` | `/` |
| `Domain` | 명시 안 함 (host-only) |
| Max-Age | 14d (슬라이딩) |

### 6.3 CSRF

- 상태 변경 메서드(POST/PATCH/DELETE) 에 대해서만 **double-submit** 토큰 검증.
- 클라이언트는 `/api/me` 응답의 `csrfToken` 을 메모리에 보관 후 `X-CSRF-Token` 헤더로 송신.
- 서버는 `csrf:<sid>` 와 헤더 값 일치 여부 확인. 불일치 시 `403 CSRF_FAILED`.
- SSE 는 GET 이므로 CSRF 대상 외.

### 6.4 만료·로그아웃

- 활동(요청) 시마다 `sid:*` TTL 을 14d 로 재설정 (슬라이딩).
- `DELETE /auth/session` → 현재 `sid` 만 삭제.
- `DELETE /auth/sessions` → `user_sids:<user_id>` 의 모든 sid 삭제 (revokeAllFor).
- 30일 절대 만료(absolute lifetime) 는 M1 범위 외(추후 ADR).

### 6.5 비밀번호 정책

- 최소 10자, 영문+숫자+기호 중 2종 이상. 클라이언트·서버 양측 검증.
- 비밀번호 변경 시 `revokeAllFor` 자동 호출.

---

## 7. 관측성 훅

### 7.1 구조화 로그 (JSON Lines)

필수 필드:

```json
{
  "ts": "2026-05-19T13:30:01.123Z",
  "level": "info",
  "service": "api" | "worker",
  "request_id": "01J...",       // 외부 X-Request-Id 또는 서버 생성
  "trace_id": "01J...",          // request_id 와 동일 — 시범 단계는 동일값 사용
  "user_id": "01J...|null",
  "job_id": "01J...|null",
  "route": "/api/jobs",
  "msg": "job enqueued",
  "extra": { "type": "dummy.sleep" }
}
```

- 비밀번호·세션 쿠키·CSRF 토큰은 **로그 금지**. 페이로드는 50KB 초과 시 절단.
- 에러 메시지는 사용자 응답용(`error.message`) 과 내부 로그(`error.stack`) 를 분리.

### 7.2 메트릭 — `/metrics` (Prometheus text)

| 이름 | 타입 | 라벨 | 의미 |
|---|---|---|---|
| `http_request_duration_seconds` | histogram | `method`,`route`,`status` | 모든 API 요청 |
| `http_requests_total` | counter | `method`,`route`,`status` | |
| `job_queue_length` | gauge | `queue` | Celery 큐 길이 (sampler) |
| `job_duration_seconds` | histogram | `type`,`outcome` | 작업 처리 시간 |
| `job_outcomes_total` | counter | `type`,`outcome` | succeeded/failed/canceled |
| `sse_clients_active` | gauge | `channel` (`user`/`job`) | 현재 SSE 연결 수 (채널별) |
| `sse_messages_sent_total` | counter | `channel`,`event` | 발송된 SSE 이벤트 |
| `queue_emitter_leader` | gauge | `instance` | sampler 단일 리더 여부 (1/0) |
| `sse_emit_to_receive_seconds` | histogram | `channel`(`user`/`job`), `client_type`=`test` | **테스트 빌드 한정** push-to-receive 지연. `_emit_at` 페이로드 기반(§5.4.3). 운영 빌드 미수집 |

- p95 산출은 카맥이 별도 대시보드에서 수행 (`docs/performance/regression-perf.md`).

### 7.3 트레이스 ID 전파

- 인입 요청에 `X-Request-Id` 가 있으면 사용, 없으면 ULID 생성.
- 응답 헤더에 동일 ID 반환.
- API → Celery 전달 시 작업 `payload._trace_id` 에 주입. 워커 로그는 동일 ID 로 식별 가능.

---

## 8. 인터페이스 변경 절차

ADR-001 확정 이후 **§4 데이터 모델 / §5 API / §6 인증** 의 변경은 다음 절차를 따른다.

1. 변경 제안 PR 에 `interface-change` 라벨 + 영향 분석 본문 포함.
2. **네이선 승인 필수** — 미승인 시 머지 차단.
3. 비호환 변경은 별도 ADR (예: ADR-002) 을 발행하여 §1 표·§4 ~ §6 본문을 갱신.
4. 호환 변경(필드 추가 등) 은 ADR-001 본문에 패치 노트 섹션을 추가하고 일자·PR 번호 기록.

§7 관측성·§3 큐 모델 내부 디테일은 ADR 수정 대상이 아니며 코드 변경으로 진행 가능 (단, 새 메트릭/이벤트 추가 시 §7.2 / §5.4 표 갱신 필수).

### 8.1 §8 게이트키퍼 운영 규칙 — 5단계 (정식 채택, 2026-05-19)

네이선이 PR 검증 시 적용하는 5단계 규칙. 본 시범 프로젝트의 핵심 거버넌스 산출물.

| 단계 | 점검 | 트리거 시 행동 |
|---|---|---|
| ① | **`interface-change` 라벨** 부착 여부 | 라벨 + 휴리스틱(②) 어느 쪽이라도 참이면 ② 진행 |
| ② | **§4·§5·§6 경로 휴리스틱** — `apps/api/.../models/`, `.../sse/`, `.../auth/`, `.../utils/metrics.py`, `.../utils/emit_timing.py`, `.../blueprints/events.py` 등 매핑 경로 변경 감지 | 정합 점검 진행 (③) |
| ③ | **컨텍스트 라인 검증 패턴** — 변경 diff 의 unchanged surrounding lines 까지 ADR 정합 점검 | 스코프 외 부정합 발견 시 통과 코멘트 + 별도 관찰 명시 + 별도 H/PR 트래킹 권고 (게이트 차단 사유 아님) |
| ④ | **SSOT 트레이스** — `docs/tasks/T*.md` (위임) ↔ `docs/qa/inspection-*.md` (검수) ↔ ADR-001 본문/패치 노트 일관성 확인 | 호환 변경: 패치 노트 추가 / 비호환 변경: ADR-002 발행 요구 |
| ⑤ | **머지 직전 head SHA 일치 검증** | 통과 코멘트 본문에 **검증 시점 head SHA 명시**. 머지 직전 PR head SHA 와 불일치 시 **통과 무효 + 재검증 요구** |

#### 운영 환경 격상 권고

시범 환경에서는 ⑤ 가 인적 검증(머지 책임자가 통과 코멘트의 SHA 와 머지 시점 SHA 비교) 으로 충분. 운영 환경 진입 시 GitHub branch protection 의 **"Require approvals on the most recent push"** + **"Require status checks to pass after re-push"** 로 자동화 격상.

#### 통과 코멘트 표준 형식

PR 코멘트 최상단에 다음 두 줄을 고정 포함한다 — 머지 책임자가 ⑤ 단계를 수행할 수 있도록.

```
검증자: 네이선 (Architect) · 검증일: YYYY-MM-DD HH:MM · 기준: ADR-001 §<해당 절>
검증 시점 head SHA: <full 40-char SHA>
```

#### SSOT 등재 위치

- **ADR-001 §8.1 (본 절)** — 1차 SSOT.
- `docs/qa/review-log.md §0` 박스 — 정민 영역 cross-reference (네이선 → 정민 위임).

---

## OWASP Top 10 (2021) 한 줄 매핑

| ID | 위협 | 본 아키텍처의 대응 (한 줄) |
|---|---|---|
| A01 | Broken Access Control | 모든 `/api/*` 는 세션 검증 + 리소스 소유자(user_id) 일치 강제, IDOR 방지. `_emit_at` 타이밍 측면 채널 차단(§5.4.3 다층 가드) |
| A02 | Cryptographic Failures | 비밀번호 argon2id, 쿠키 Secure+HttpOnly, 운영 HTTPS 강제(HSTS) |
| A03 | Injection | ORM 파라미터 바인딩, 입력 검증(스키마 기반), 작업 payload 화이트리스트 |
| A04 | Insecure Design | ADR-001 로 위협 모델·상태 머신·경계 명시, 변경은 §8 절차 |
| A05 | Security Misconfiguration | `Secure`/`HttpOnly`/`SameSite`/CSP 기본값 명시, `/metrics` 내부망 한정 |
| A06 | Vulnerable Components | 수진 리서치(T2) 에서 CVE 스캔 결과 반영, `pip-audit`·`npm audit` 게이트 |
| A07 | ID & Auth Failures | 세션 revoke + 비밀번호 변경 시 revokeAllFor, 로그인 5 req/min/IP |
| A08 | Software & Data Integrity | Idempotency-Key + UNIQUE 제약, Celery `acks_late` 로 중복/유실 방지 |
| A09 | Security Logging Failures | 구조화 로그(§7.1), 인증 실패·CSRF 실패 카운트 메트릭. `_emit_at` 로그 출력 금지(§5.4.3) — 로그 사이드채널 방지 |
| A10 | SSRF | 사용자 입력으로 외부 HTTP 호출 안 함 (시범 작업은 더미). 추후 도입 시 별도 ADR |

---

## 비기능 요구 메모 (게이트 기준 도출 근거)

| 항목 | 목표 (제임스 상위 결정) | 본 ADR 의 구조적 근거 |
|---|---|---|
| API p95 | < 200ms | Flask + Redis 직접 enqueue, ORM N+1 회피 (jobs/job_events 인덱스 §4.1) |
| SSE 푸시 지연 p95 | < 500ms | Redis pub/sub 직결, API 가 메모리에서 SUBSCRIBE → 즉시 write |
| 동시 1k 작업 | 안정 | Celery worker 수평 확장 + acks_late, 큐 길이 메트릭으로 감시 |
| 가용성 | 시범 — best effort | 단일 인스턴스 허용 (R-004), 운영용 멀티화는 별도 ADR |

---

## 후속 작업 (마크·정민·카맥에게 인계)

| 영역 | 담당 | 기대 산출 |
|---|---|---|
| 스키마 마이그레이션 (§4.1) + ORM 모델 | 마크 | Alembic 첫 마이그레이션 |
| Flask blueprint 구조 + auth 미들웨어 + CSRF | 마크 | `/auth`, `/api/me` 라우트 |
| Celery 부트스트랩 (큐·재시도·routes) | 마크 | `celery_app.py` + 더미 작업 |
| SSE 핸들러 + Redis Stream 백필 | 마크 | `/api/events/jobs` |
| 회귀 시나리오 (8건) | 정민 | `docs/qa/scenarios.md` |
| perf budget·메트릭 대시보드 | 카맥 | `docs/performance/regression-perf.md` |

## 패치 노트

- **2026-05-19 15:15 — Patch 4 (네이선)**: §8 게이트키퍼 운영 규칙 5단계 영구 등재(§8.1 신설). CTO 추인(2026-05-19 15:11) 반영. 핵심 거버넌스 SSOT — 통과 코멘트 표준 형식(검증자/검증일/기준/검증 시점 head SHA 2줄) + 운영 환경 격상 권고(branch protection "Require approvals on the most recent push" + "Require status checks to pass after re-push"). docs/qa/review-log.md §0 박스 cross-reference 는 정민 위임. 호환 변경(본문 추가만).
- **2026-05-19 13:58 — Patch 2 + 3 (네이선, 동일 PR 묶음)**: T6(카맥) `_emit_at` 측정 훅 + 정민 SM-4 회귀 명세 수동 retry 정책. 모두 호환 변경.
  - **Patch 2 (`_emit_at`)**: §5.4.3 신설(필드·포맷·다층 가드 5층·마크 구현 분기). §7.2 에 `sse_emit_to_receive_seconds` 히스토그램 추가(테스트 빌드 한정, `client_type=test` 라벨). §1.2 흐름 7번 추가. OWASP A01·A09 한 줄 보강(타이밍 측면 채널·로그 사이드채널 차단). 노출 AND 조건: `ENABLE_EMIT_AT=true` ∧ `X-Perf-Client: test`. 출처: `docs/performance/baseline.md §4.1`, `docs/qa/inspection-T6-carmack.md`.
  - **Patch 3 (수동 retry 정책)**: §3.2 를 자동(Celery)/수동(PATCH) 으로 분할하고 허용 상태(`failed`/`canceled`) · 거부 상태(`succeeded` → `409 INVALID_TRANSITION`) 명시. §4.3 상태 머신에 종결 상태별 액션 표 추가. §5.1 PATCH 비고 갱신. 오류 코드 카탈로그에 `INVALID_TRANSITION` 추가. `succeeded` 재실행은 후속 ADR 의 `clone` 액션으로 분리(M1 외). 출처: `docs/qa/scenarios.md SM-4`.
- **2026-05-19 13:50 — Patch 1 (네이선)**: T3(수영) UI 인벤토리 정합 + T2(수진) 의존성 감사 반영. 호환 변경(추가만, 기존 인터페이스 변경 없음).
  - §0 TL;DR: SSE 채널을 2개로 명시, Redis 버전·보안 SSOT 한 줄 추가.
  - §4.2: Redis 7.4.2+ 고정 + 보안 설정 SSOT(R-006) 추가. 작업 상세 채널(`events:jobs:job:*`)·시스템 채널(`events:system:queue`)·sampler 락(`heartbeat:queue_emitter`) 키 추가.
  - §5.1: `/api/events/jobs/:id` 엔드포인트 신설 (작업 상세 전용, 소유자 검증).
  - §5.3: 단일 채널 설명을 §5.3.1(사용자) + §5.3.2(작업 상세) 로 분할. 다중 SUBSCRIBE 메커니즘 명세.
  - §5.4: 이벤트 카탈로그에 `queue.counts`·`queue.workers`·`log_line` 3종 추가, 채널(U/D)·빈도/정책 컬럼 추가. §5.4.1 sampler 단일 리더 메커니즘, §5.4.2 `log_line` 분리 근거 추가.
- 2026-05-19: 초안 작성 및 Accepted (네이선). PR 없음(분석 모드 종료 직후 개발 모드 진입 ADR).
