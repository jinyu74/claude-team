# 보안 Audit — 실시간 작업 큐 대시보드 (M1)

- 최종 갱신: 2026-05-19 by 정민
- 상위: [ADR-001](../decisions/ADR-001-architecture.md) §6·§7·OWASP 매핑 표, [T5](../tasks/T5-qa-jungmin.md)
- 적용: 마크의 모든 PR 머지 게이트. CRITICAL/HIGH 0건 충족 시에만 머지 허용.
- 평가 등급: CRITICAL → 머지 차단 / HIGH → 머지 차단 / MEDIUM → 코멘트 후 머지 허용 / LOW → 노트.

## 0. 사용 방법

### 0.1 PR 별 적용

정민이 PR 리뷰 시 본 문서의 체크리스트를 위에서 아래로 실행하고, 각 항목별로 다음을 [review-log.md](review-log.md) 의 PR 행에 기록.

```text
A01-1: ✅ / A01-2: ⚠️ MED (소유자 검증 누락 - line 42) / ...
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0
결론: 머지 허용 (MEDIUM 후속)
```

### 0.2 자동화 보조 도구

| 도구 | 용도 | PR 별 실행 |
|---|---|---|
| `pip-audit` | Python 의존성 CVE | CI 게이트 |
| `npm audit --audit-level=high` | JS 의존성 CVE | CI 게이트 |
| `ruff`, `pyright` | 정적 분석 (보안 lint 포함: `S` rule set) | CI 게이트 |
| `eslint` (`@typescript-eslint`, `eslint-plugin-security`) | JS/TS 보안 lint | CI 게이트 |
| `bandit` (선택) | Python 보안 정적 분석 | 주간 audit |
| `tests/security/headers.spec.ts` | 보안 헤더 응답 검증 | CI 게이트 |
| `tests/security/log-grep.spec.ts` | 로그 비밀 누설 grep | CI 게이트 |
| Playwright a11y 스캔 (axe-core) | 색 대비·focus visible | CI 게이트 |

---

## A01 — Broken Access Control

> ADR-001 OWASP 매핑: 모든 `/api/*` 는 세션 검증 + 리소스 소유자(user_id) 일치 강제, IDOR 방지.

| ID | 점검 항목 | 검증 방법 | 등급 (위반 시) |
|---|---|---|---|
| A01-1 | 세션 미인증 요청은 `/api/*` 전체에서 `401 UNAUTHENTICATED` | `tests/security/auth.spec.ts:unauth-blocks-all` (모든 라우트 enumerate) | **CRITICAL** |
| A01-2 | `/api/jobs/:id` GET·PATCH 가 **소유자(user_id) 검증**. 타인 작업 접근 시 `404` (존재 비공개) | `tests/security/idor.spec.ts:cross-user-job` | **CRITICAL** |
| A01-3 | `/api/events/jobs/:id` (작업 상세 SSE) 도 소유자 검증. 타인 작업 구독 시 `403 FORBIDDEN` 또는 `404` | `tests/security/idor.spec.ts:cross-user-sse` | **CRITICAL** |
| A01-4 | `/api/events/jobs` (사용자 채널) 이 사용자의 채널만 SUBSCRIBE — 타인 `user_id` 채널 누설 차단 | 코드 리뷰 (`subscribe` 인자가 세션의 `user_id` 인지) + Redis MONITOR 1회 | HIGH |
| A01-5 | `/metrics` 는 내부망 한정 (외부 접근 시 `404` 또는 `403`) | `tests/security/metrics-acl.spec.ts` — 운영용 헤더/IP 화이트리스트 가정 시 dev 환경에서는 X-Forwarded-For mock 으로 검증 | HIGH |
| A01-6 | 권한 분리 — 일반 사용자가 다른 사용자의 세션을 revoke 할 수 없음 | `tests/security/auth.spec.ts:revoke-others-blocked` (`DELETE /auth/sessions` 은 자기 세션만) | **CRITICAL** |
| A01-7 | 작업 상태 머신 우회 시도 — `PATCH /api/jobs/:id {status:"succeeded"}` 같이 종결 상태 강제 설정 시 `400 VALIDATION_FAILED` | `tests/security/state-tampering.spec.ts` | HIGH |
| A01-8 | URL 패턴 추측·열거 방어 — `/api/jobs/{random-uuid}` 가 본인 작업이 아니면 `404`. 존재 여부를 응답 시간/메시지로 누설하지 않음 | `tests/security/idor.spec.ts:timing-and-message` (응답 시간 분산 ≤ 30%) | HIGH |
| A01-9 | **`_emit_at` 페이로드 누출 차단 (타이밍 오라클 측면 채널)** — ADR-001 §5.4.3 다층 가드. 노출 AND 조건: `ENABLE_EMIT_AT=true` ∧ `X-Perf-Client: test` 둘 다 만족하는 응답에만 살아남는다. 둘 중 하나라도 미충족 시 응답 본문에 `_emit_at` 키 부재 | `tests/security/payload-strip.spec.ts` — 평범한 클라이언트(`X-Perf-Client` 헤더 없음) 가 받은 SSE 응답·REST 응답 모두에서 `_emit_at` 키 부재 확인. `ENABLE_EMIT_AT` 미설정 환경에서도 동일 검증 | **CRITICAL** |

**잔여 위협 메모.**
- `priority` 필드 — 일반 사용자가 `priority:10 (high)` 를 자유 설정하면 DoS 위험. M1 인터페이스는 허용이지만 `tests/security/quota.spec.ts` 에서 사용자별 `high` 큐 분당 N건 제한을 별도 ADR 후 도입 권장. 현 단계 LOW (관찰).

---

## A02 — Cryptographic Failures

> ADR-001: 비밀번호 argon2id, 쿠키 Secure+HttpOnly, 운영 HTTPS 강제(HSTS).

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A02-1 | 비밀번호 해시 = **argon2id** with `memory_cost=65536 (64MB)`, `time_cost=3`, `parallelism=1` | `tests/security/password-hash.spec.ts` — `argon2.PasswordHasher` 설정 dump 또는 해시 prefix `$argon2id$v=19$m=65536,t=3,p=1$...` 검증 | **CRITICAL** |
| A02-2 | bcrypt·MD5·SHA1·plain 흔적 없음 | 코드 grep `bcrypt`, `hashlib.md5`, `hashlib.sha1` (서명/HMAC 외 용도) | **CRITICAL** |
| A02-3 | 쿠키 속성 — `HttpOnly`, `Secure` (운영), `SameSite=Lax`, `Path=/`, host-only (`Domain` 명시 안 함) | 시나리오 1 step 1 + `tests/security/cookie-flags.spec.ts` | **CRITICAL** |
| A02-4 | 운영 빌드에서 `Secure=false` 가 머지되지 않음 | `if NODE_ENV in ('test','dev')` 가드 + 환경별 응답 헤더 스냅샷 | HIGH |
| A02-5 | HSTS — `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` (운영) | `tests/security/headers.spec.ts` | HIGH |
| A02-6 | 세션 ID 엔트로피 — 128-bit ULID. 외부 추측 불가 | 코드 리뷰 + `Math.random()` 같은 약한 PRNG 사용 흔적 부재 (`crypto.randomBytes` / `secrets.token_bytes`) | HIGH |
| A02-7 | CSRF 토큰 — 128-bit, 세션과 1:1 바인딩 (`csrf:<sid>`) | 코드 리뷰 + `tests/security/csrf.spec.ts:token-binding` (세션 A 의 토큰을 세션 B 에 사용 → 403) | HIGH |
| A02-8 | 비밀번호 reset/변경 시 `revokeAllFor` 호출 (ADR §6.5) | `tests/security/password-change.spec.ts` | HIGH |

---

## A03 — Injection

> ADR-001: ORM 파라미터 바인딩, 입력 검증(스키마 기반), 작업 payload 화이트리스트.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A03-1 | SQL — 모든 쿼리가 ORM/파라미터 바인딩. 문자열 concat·f-string 으로 SQL 작성 흔적 없음 | 코드 grep `execute\(.*\+`, `cursor.execute\(.*f"`, `cursor.execute\(.*%`. ruff `S608` (hardcoded-sql-expression) | **CRITICAL** |
| A03-2 | 입력 검증 — 모든 `POST/PATCH` 본문이 스키마 기반 (`pydantic` / `zod`) | 라우트 enumerate + 각 라우트의 스키마 객체 존재 확인 | HIGH |
| A03-3 | `payload` JSONB 화이트리스트 — `type` 별로 허용 키만. unknown 필드 reject (`extra="forbid"`) | `tests/security/payload-whitelist.spec.ts` | HIGH |
| A03-4 | OS command — 외부 명령 실행 없음. 있다면 `shell=False` + arg list | 코드 grep `subprocess`, `os.system`, `os.popen`. ruff `S602`, `S605` | **CRITICAL** |
| A03-5 | 템플릿 — 서버사이드 HTML 렌더링 없음 (SPA). 있다면 자동 escape 활성 + `Markup`/`safe` 흔적 검토 | 코드 grep `render_template`, `Markup`, `\|safe` | HIGH |
| A03-6 | NoSQL/Redis — Redis 키 생성 시 사용자 입력 sanitize (`:`/`\n` 등 메타문자) | 코드 리뷰 + `tests/security/redis-key-injection.spec.ts` (악성 `user_id` 로 다른 채널 접근 시도) | HIGH |
| A03-7 | 로그 인젝션 — 로그 라인에 사용자 입력의 CRLF 가 그대로 출력되지 않음 | `tests/security/log-injection.spec.ts` — 사용자 email 에 `\nFAKE LOG` 포함 후 로그 escape 확인 | MEDIUM |

---

## A04 — Insecure Design

> ADR-001: ADR 로 위협 모델·상태 머신·경계 명시, 변경은 §8 절차.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A04-1 | `/api/*` 또는 `/auth/*` 인터페이스 변경 PR 에 `interface-change` 라벨 + 네이선 승인 | GitHub 라벨 + Required Reviewers 정책 | HIGH |
| A04-2 | 상태 머신 단방향 — 종결 상태에서 재진입 거절 | 시나리오 4·5 + [regression.md](regression.md) | HIGH |
| A04-3 | 새 이벤트/메트릭 추가 시 ADR §5.4 / §7.2 표 갱신 PR 동반 | 리뷰 시 확인 | MEDIUM |
| A04-4 | 신규 외부 호출·SSRF 후보 도입 시 별도 ADR | 코드 grep `requests`, `httpx`, `urllib`. M1 범위에서는 0건 | HIGH (도입 시) |

---

## A05 — Security Misconfiguration

> ADR-001: `Secure`/`HttpOnly`/`SameSite`/CSP 기본값 명시, `/metrics` 내부망 한정.

### A05.a — 보안 헤더 (응답 검증)

`tests/security/headers.spec.ts` 가 모든 HTML 응답 + 대표 JSON 응답에 다음을 검증.

| 헤더 | 기대값 | 등급 (누락 시) |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` (운영) | HIGH |
| `X-Content-Type-Options` | `nosniff` | HIGH |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | MEDIUM |
| `X-Frame-Options` | `DENY` (또는 CSP `frame-ancestors 'none'`) | HIGH |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` 최소 | LOW |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'nonce-...'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'` | HIGH |
| `Cache-Control` (SSE) | `no-cache, no-transform` | MEDIUM |

### A05.b — 환경 분리

| ID | 점검 항목 | 등급 |
|---|---|---|
| A05-1 | `.env`, `*.pem`, `*.key`, `id_rsa`, `credentials.json` 가 `.gitignore` 에 등재 | **CRITICAL** |
| A05-2 | 운영 빌드에서 `DEBUG=False`, Flask `app.debug = False`, 디버거·콘솔 비활성 | HIGH |
| A05-3 | `/metrics` 가 운영에서 내부망 한정 (`X-Forwarded-For` 또는 별도 포트) | HIGH |
| A05-4 | Redis `requirepass` 설정 + 바인딩 `127.0.0.1`/사설망 (ADR §4.2 R-006) | **CRITICAL** |
| A05-5 | Redis `FLUSHALL`, `CONFIG` 가 `rename-command ""` 으로 비활성 (R-006) | **CRITICAL** |
| A05-6 | Redis 버전 ≥ 7.4.2 (RediShell CVE-2025-49844 픽스). `docker-compose.yml` 의 image tag 확인 | **CRITICAL** |
| A05-7 | PG 사용자 — 최소 권한 (앱 사용자는 `CREATE DATABASE`, `CREATEROLE` 권한 없음) | HIGH |
| A05-8 | 디폴트 비밀번호 흔적 없음 (`postgres/postgres`, `admin/admin` 등) | **CRITICAL** |

---

## A06 — Vulnerable & Outdated Components

> ADR-001: `pip-audit`·`npm audit` 게이트, 수진(T2) 리서치 결과 반영.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A06-1 | `pip-audit` 실행 시 HIGH/CRITICAL 0건 | CI step + PR comment | HIGH |
| A06-2 | `npm audit --audit-level=high` 0건 | CI step | HIGH |
| A06-3 | Redis 이미지 tag ≥ 7.4.2 (R-006) | `docker-compose.yml` grep | **CRITICAL** |
| A06-4 | Celery, Flask, SQLAlchemy 등 핵심 의존성이 수진의 `docs/analysis/dependency-audit.md` 권장 버전 이상 | 주간 audit (정민) + 새 의존성 추가 PR 시 즉시 | HIGH |
| A06-5 | `package-lock.json` / `requirements.txt` (또는 `pyproject.toml` + `uv.lock`/`poetry.lock`) 가 PR 에 포함 — 잠금 파일 없는 의존성 추가 금지 | PR 파일 변경 확인 | MEDIUM |
| A06-6 | 전이 의존성에서 사후 발견된 CVE 는 주간 audit 에서 추적 → `docs/qa/review-log.md` 부록 | 주간 정민 task | — |

---

## A07 — Identification & Authentication Failures

> ADR-001: 세션 revoke + 비밀번호 변경 시 revokeAllFor, 로그인 5 req/min/IP.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A07-1 | 로그인 실패 — `5 req/min/IP` rate limit. 초과 시 `429 RATE_LIMITED` + `Retry-After` 헤더 | `tests/security/rate-limit.spec.ts` (10 req 발사 → 6번째부터 429) | HIGH |
| A07-2 | 로그인 실패 메시지 통일 — `"이메일 또는 비밀번호가 일치하지 않습니다"`. 존재하는 이메일과 부재 이메일의 응답이 동일 (사용자 열거 방어) | `tests/security/auth.spec.ts:enumeration` (메시지 + 응답 시간 분산 ≤ 30%) | HIGH |
| A07-3 | 비밀번호 정책 — 최소 10자, 영문+숫자+기호 중 2종 이상. 클라이언트·서버 양측 검증 | `tests/security/password-policy.spec.ts` — `1234567890`, `abcdefghij` 같은 약한 비밀번호 reject | HIGH |
| A07-4 | 세션 슬라이딩 — 활동 시 TTL 14d 로 리셋 | `tests/security/session-sliding.spec.ts` (요청 사이 TTL 증가 확인) | MEDIUM |
| A07-5 | `DELETE /auth/sessions` (revokeAllFor) → 모든 활성 세션 무효화 (시나리오 1) | 시나리오 1 step 6~8 | **CRITICAL** |
| A07-6 | 비밀번호 변경·reset 후 자동 revokeAllFor (ADR §6.5) | `tests/security/password-change.spec.ts` | HIGH |
| A07-7 | 로그인 폼 — `autocomplete="current-password"` 등 표준 속성. 폼 외부 secret 입력 필드에 `type="password"` | 코드 리뷰 + a11y 스캔 | LOW |

---

## A08 — Software & Data Integrity Failures

> ADR-001: Idempotency-Key + UNIQUE 제약, Celery `acks_late` 로 중복/유실 방지.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A08-1 | `jobs.idempotency_key` UNIQUE `(user_id, idempotency_key)` 강제 | 마이그레이션 DDL 검사 + 시나리오 6 | HIGH |
| A08-2 | Redis `idem:<uid>:<key>` 짧은 락 (60s) 으로 동시 요청 직렬화. 5xx 누수 없음 | 시나리오 6 step 5 | HIGH |
| A08-3 | Celery `acks_late=True` + `task_reject_on_worker_lost=True` (ADR §3.4) | `celery_app.py` 코드 리뷰 | HIGH |
| A08-4 | 의존성 무결성 — `package-lock.json` / lock 파일 위변조 방지 (CI 가 lock 변경 시 명시 승인 요구) | PR 라벨 정책 | MEDIUM |
| A08-5 | `event_ulid` UNIQUE — `job_events.event_ulid` 의 UNIQUE 제약 (ADR §4.1) 으로 중복 SSE 발행 방지 | DDL 검사 + `tests/integration/event-dedup.spec.ts` (마크 작성) | MEDIUM |
| A08-6 | 신뢰되지 않은 deserialization 부재 — `pickle`, `marshal` 사용 흔적 없음 (Celery serializer = JSON 강제) | `celery_app.conf.task_serializer = 'json'`, `accept_content = ['json']` 확인. 코드 grep `pickle`, `marshal` | **CRITICAL** |

---

## A09 — Security Logging & Monitoring Failures

> ADR-001 §7.1: 구조화 로그, 인증 실패·CSRF 실패 카운트 메트릭.

### A09.a — 비밀 누설 grep (CRITICAL)

`tests/security/log-grep.spec.ts` 가 다음 패턴이 **모든 로그 출력에 0건** 임을 검증. 매 PR CI 게이트.

| 패턴 | 대상 | 등급 |
|---|---|---|
| `password=`, `"password":` | 평문 비밀번호 노출 | **CRITICAL** |
| `Authorization: Bearer ` | 인증 헤더 노출 | **CRITICAL** |
| `Cookie: sid=`, `sid=01J`, `\bsid:` (단, 키 prefix 형태 `sid:*` 는 허용. 실제 값은 금지) | 세션 쿠키 노출 | **CRITICAL** |
| `csrf:01J`, `X-CSRF-Token: 01J` | CSRF 토큰 노출 | **CRITICAL** |
| `argon2id$...` (해시 자체) | 비밀번호 해시 노출 | HIGH |
| `Traceback`, `/Users/`, `/home/` | stack trace · 절대경로 노출 (운영 응답 본문에서만 검사. 내부 로그는 허용) | HIGH (응답 본문) / LOW (내부 로그) |
| `_emit_at`, `monotonic_ns` | 타이밍 측면 채널 — **로그 출력 금지** (ADR §5.4.3 마지막 가드). 평범한 클라이언트 응답 본문에서도 동일 grep 0건 | **CRITICAL** (응답 본문) / **CRITICAL** (로그) |

검증 방법 — 시나리오 1·2·3 실행 직후 worker·api 로그 파일을 `log-grep` 헬퍼로 1회 스캔. 매치 1건 = CRITICAL.

**`_emit_at` 보강 (ADR-001 Patch 2, §5.4.3).** A01-9 와 짝. `tests/security/payload-strip.spec.ts` 는 다음 4 환경을 모두 검증한다 — `_emit_at` 응답·로그 동시 누출 0 임을 보장.

| 환경 | 클라이언트 헤더 | 기대 결과 |
|---|---|---|
| 운영 (`ENABLE_EMIT_AT` 미설정 또는 `false`) | (헤더 무관) | 응답 본문에 `_emit_at` 키 부재. 페이로드 자체에 필드 없음 |
| 테스트 빌드 (`ENABLE_EMIT_AT=true`) + 평범한 클라이언트 | `X-Perf-Client` 없음 | 응답 본문에 `_emit_at` 키 부재 (직렬화 strip) |
| 테스트 빌드 + 임의 헤더 | `X-Perf-Client: prod` (`test` 외 임의 값) | 응답 본문에 `_emit_at` 키 부재 (헤더 값 정확 일치 검증) |
| 테스트 빌드 + 테스트 클라이언트 | `X-Perf-Client: test` | 응답 본문에 `_emit_at` 살아남음 (정상 측정 경로) |

로그 출력 금지는 환경·헤더 무관 — 4 환경 모두에서 worker·api 로그 grep 결과 0건이어야 한다. 1건이라도 매치 = CRITICAL.

### A09.b — 메트릭·관측성

| ID | 점검 항목 | 등급 |
|---|---|---|
| A09-1 | 인증 실패 카운터 — `auth_failures_total{reason="bad_password|user_not_found|rate_limited"}` 메트릭 노출 | HIGH |
| A09-2 | CSRF 실패 카운터 — `csrf_failures_total` | HIGH |
| A09-3 | rate limit 트리거 카운터 — `rate_limit_hits_total{route}` | MEDIUM |
| A09-4 | `request_id` 가 모든 로그·응답에 일관 출력 (ADR §7.1) | HIGH |
| A09-5 | `error.message` 와 `error.stack` 분리 — 응답에는 message, 로그에는 stack | HIGH |

---

## A10 — Server-Side Request Forgery (SSRF)

> ADR-001: 사용자 입력으로 외부 HTTP 호출 안 함. 추후 도입 시 별도 ADR.

| ID | 점검 항목 | 검증 방법 | 등급 |
|---|---|---|---|
| A10-1 | 사용자 payload 로 외부 HTTP 호출 없음 | 코드 grep `requests.`, `httpx.`, `urllib.request`, `fetch(` (서버사이드). 결과 0건 또는 화이트리스트 URL 만 | HIGH (도입 시) |
| A10-2 | 작업 payload `dummy.sleep` 등 시범 작업이 외부 호출 시도 안 함 | 워커 코드 리뷰 | HIGH |
| A10-3 | webhook/redirect URL 입력 받는 엔드포인트 없음 (M1 범위 외) | 라우트 enumerate | — |

> M1 범위에서는 SSRF 표면이 사실상 0. 추후 외부 호출 도입 시 본 섹션을 확장하고 `requests` 에 `allowed_hosts` 화이트리스트·내부 IP block 적용 + 별도 ADR.

---

## 디자인 시스템 게이트 (수영 인계)

a11y 미달은 머지 차단. `tests/a11y/contrast.spec.ts` (axe-core + Playwright) 가 검증.

### 색 대비 검증 쌍 (수영 `docs/analysis/ui-tokens.md §대비 검증 체크포인트` SSOT)

| 전경 | 배경 | 최소 대비 | 등급 (미달 시) |
|---|---|---|---|
| `--color-text` | `--color-surface` | 4.5:1 | HIGH |
| `--color-text-muted` | `--color-surface` | 4.5:1 | HIGH |
| `--color-status-pending` | `--color-status-pending-bg` | 4.5:1 | HIGH |
| `--color-status-running` | `--color-status-running-bg` | 4.5:1 | HIGH |
| `--color-status-done` | `--color-status-done-bg` | 4.5:1 | HIGH |
| `--color-status-failed` | `--color-status-failed-bg` | 4.5:1 | HIGH |
| `--color-border` | `--color-surface` | 3:1 | MEDIUM |
| `--color-focus-ring` | 주변 배경 | 3:1 | HIGH |

### 포커스 링

| ID | 점검 항목 | 등급 |
|---|---|---|
| FOCUS-1 | 인터랙티브 요소(button/link/input/[tabindex]) 에 `:focus-visible` 시 `outline: 2px solid var(--color-focus-ring); outline-offset: 2px` 적용 | HIGH |
| FOCUS-2 | CSS `outline: none` / `outline: 0` 발견 시 차단 (라이브러리 default 포함, 명시적 override 없으면 금지) | HIGH |

검증 — `tests/a11y/focus-ring.spec.ts` 가 모든 인터랙티브 요소를 Tab 으로 순회하며 outline 계산값을 검사. 0px 발견 = 차단.

---

## 사전 합의 사항 (마크 회신 필요 — 제임스가 마크에 별도 위임 완료)

- **Q-S1.** `tests/security/log-grep.spec.ts` 가 읽을 로그 출력 경로 — stdout 캡처? 파일? Docker 컨테이너 로그? E2E 셋업에서 worker·api 모두 단일 파일/stdout 으로 일원화하기를 권장.
- **Q-S2.** `pip-audit` / `npm audit` 의 `--ignore-vuln` 화이트리스트 정책 — 마크가 무시할 CVE 를 정민 승인 없이 추가하지 않도록 `.audit-ignore` 파일을 PR 로 받기.
- **Q-S3.** Playwright a11y 스캔의 실행 시점 — 모든 PR vs UI 변경 PR 만. **모든 PR 권장** (a11y 회귀가 백엔드 변경에서도 발생).

회신은 `team-send 정민 "[T5-Sec] Q-S1/2/3: ..."` 로.
