# PR 머지 게이트 리뷰 로그

- 최종 갱신: 2026-05-19 by 정민
- 상위: [T5](../tasks/T5-qa-jungmin.md), [scenarios.md](scenarios.md), [security-audit.md](security-audit.md), [regression.md](regression.md)
- 운영자: 정민. 마크의 모든 PR 은 본 로그의 게이트를 통과해야 머지.

## 0. 게이트 절차

### 0.1 실행 순서 (정민이 PR 마다)

```
1. PR 범위 식별 (변경 파일·인터페이스 변경 여부)
2. CI 그린 확인:
   - 단위/통합 테스트 통과 + 커버리지 ≥ 80% (pytest-cov, vitest)
   - 정적분석 ruff·pyright·eslint·tsc --noEmit 0 error
   - pip-audit / npm audit 0 HIGH+
3. 보안 audit 체크리스트 실행 (security-audit.md) — CRITICAL/HIGH 0건
4. 회귀 게이트 매트릭스 실행 (regression.md §회귀 게이트 실행 매트릭스)
5. 해당 영역 E2E 시나리오 실행 (scenarios.md)
6. (인터페이스 변경 PR) 네이선 승인 확인
7. 본 로그에 PR 행 추가 + 결론 코멘트 (PR 본문)
```

### 0.2 등급 (audit·regression 공통)

| 등급 | 머지 영향 |
|---|---|
| **CRITICAL** | 머지 차단. 동일 PR 내 수정. |
| **HIGH** | 머지 차단. 동일 PR 내 수정. |
| **MEDIUM** | 코멘트 후 머지 허용. 후속 Sub-task 생성. |
| **LOW** | 노트만. 후속 Sub-task 선택. |

### 0.3 PR 코멘트 템플릿

PR 본문 코멘트로 다음을 그대로 게시.

```markdown
## 정민 머지 게이트 — PR #__

**결론.** [머지 허용 / 머지 보류 / 머지 차단]

### 자동 게이트
- 단위/통합 테스트: __ (커버리지 __%)
- 정적분석: ruff __ / pyright __ / eslint __ / tsc __
- 의존성 audit: pip-audit __ / npm audit __

### 보안 audit (CRITICAL/HIGH 0건 필수)
- A01~A10: __ (상세는 본 행 참조)

### 회귀 매트릭스
- 실행 항목: __ (영향 범위)
- 결과: __

### E2E 시나리오 (영향 범위)
- __

### 발견 사항 (등급별)
- **CRITICAL** (__건): __
- **HIGH** (__건): __
- **MEDIUM** (__건): __
- **LOW** (__건): __

### 후속
- __
```

---

## 1. PR 별 로그 (운영 시작 후 행 추가)

> 첫 마크 PR 부터 한 행씩 추가. 인덱스 컬럼은 ID 가 아니라 PR 번호.

| 일자 | PR # | 제목 (요약) | 범위 (Jira) | CI 그린 | 보안 audit | 회귀 | E2E 시나리오 | CRITICAL | HIGH | MEDIUM | LOW | 결론 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-19 | #3 | jobs API + worker Phase 1 | 작업 제출·조회 / 워커·Celery | ✅ 58 passed, 82.00% cov / ❌ ruff 66 / ❌ pyright 17 / ❌ pip-audit 미설치 | ❌ A01·A03·A08 위반 다수 | ❌ §1 SM-1/2 envelope 위반, §6 IDEM lock race 누설 | ❌ #2 이벤트 카탈로그 회귀, #6 멱등 race 미수정 | **5** | **8** | **11** | **2** | **차단** | [상세](#pr-3-상세) |

### 행 작성 규칙

- "결론" 컬럼은 `허용` / `보류` / `차단` 3종.
- "비고" 컬럼에는 차단 사유 또는 후속 Sub-task 키.
- 머지 후에도 행은 보존 (감사 추적).

---

### PR #3 상세

**결론.** **머지 차단** (CRITICAL 5 / HIGH 8 / MEDIUM 11 / LOW 2). 핵심 사유 — ADR §5.4 이벤트 카탈로그 회귀(이름·페이로드) + ADR §5.5 응답 envelope 미준수 + Idempotency lock race 미처리 + 정적분석·의존성 게이트 미통과.

**자동 게이트.**
- 단위/통합 테스트 ✅ 58 passed (마크 보고 54 — +4 차이는 conftest 정합 메모)
- 커버리지 ✅ TOTAL 82.00% (마크 보고 81.45% — 측정 시점 차이)
- 정적분석 ❌ ruff 66 errors (I001×37 / F401×13 / E501×5 / UP017×4 / S106/S107/S105×4 / 기타×3) — 54건은 `ruff check --fix` 1회 해결 가능
- 정적분석 ❌ pyright 17 errors — SQLAlchemy 모델 생성자 7건은 false positive 가능, `xadd` `bytes/str` 2건 + `pubsub.listen()` Awaitable 1건은 redis-py 타입 스텁 이슈
- 의존성 ❌ pip-audit 미설치 — A06-1 게이트 실행 불가 (마크 회신 Q-S2 후 `.audit-ignore` 정책 확정 + 설치)

**발견 사항 (등급별).**

#### CRITICAL (머지 차단)

- **C1. `services/sse.py:48-49, services/job.py:42,64` — 이벤트 페이로드 전체 `job.to_dict()` 발행**. `celery_task_id` · `idempotency_key` · `payload` 전체가 SSE 응답으로 노출. ADR §5.4 카탈로그 위반 (`job.submitted` 은 `{jobId, type, priority, createdAt}` 4 키만, `job.started` 은 `{jobId, startedAt, attempts}` 3 키만). 정보 누설 + 인터페이스 회귀.
- **C2. `services/job.py` — `job_events` INSERT 부재**. ADR §1.2 흐름 1 의 `job_events(submitted)` 기록 누락. 모델 (`JobEvent`) 은 정의되어 있으나 어디서도 INSERT 안 함. → 시나리오 7 (SSE 끊김 백필) 의 `event_ulid` SSOT 가 깨짐. 회귀 매트릭스 SSE-1 (catchup_overflow) 통과 불가.
- **C3. `services/job.py:42` — `job.created` 이벤트 이름**. ADR §5.4 카탈로그는 `job.submitted`. → 시나리오 2 의 `recorder.untilEvent("job.submitted")` 1초 timeout 으로 실패.
- **C4. `services/job.py:64` — `job.running` 이벤트 이름**. ADR §5.4 카탈로그는 `job.started`. → 시나리오 2 의 `recorder.untilEvent("job.started")` 실패.
- **C5. `services/sse.py:30-50` — 모든 이벤트를 사용자 채널과 작업 상세 채널 양쪽에 같은 데이터로 발행**. ADR §5.4 의 채널 분리 정책 위반 (`job.submitted` 은 U 만, `progress` 은 U(throttled)·D(raw) 등 이벤트별 채널 명세). + 사용자 채널 1s throttle 미구현. 시나리오 2 step 4 (1s throttle) 검증 불능.

#### HIGH (머지 차단)

- **H1. `blueprints/jobs.py:101-141` — PATCH cancel 인터페이스 `action=cancel`**. ADR §5.1 PATCH body 는 `{status:"canceled"}` 명시. **인터페이스 변경 PR** 이므로 §8 절차상 **네이선 승인 필요** — 본 PR 에는 ADR Patch 또는 라벨 없음.
- **H2. `services/job.py:25-28` — Idempotency lock race**. `acquire_idempotency_lock` 실패 + existing None 분기에서 그대로 INSERT 진행 → PG UNIQUE 위반 → 500. 시나리오 6 step 5 (Promise.all 동일 키) 의 "5xx 아님" 조건 위반. A08-2 + IDEM-1 회귀.
- **H3. 응답 envelope 위반 (전영역)**. ADR §5.5 의 `{"error":{"code":"...","message":"..."}}` 미준수. 현 코드 — `jobs.py:29 {"error":"CSRF token invalid"}` (CSRF_FAILED 코드 없음), `jobs.py:41 {"error":"type is required"}` (VALIDATION_FAILED 없음), `jobs.py:47, 97, 111, 115` 모두 동일. `session.py:24 {"error":"Unauthorized"}` (UNAUTHENTICATED 없음). `events.py:85 {"error":"Not found"}` (NOT_FOUND 없음). 시나리오 1 step 3 의 `error.code == "CSRF_FAILED"` 검증 불통과.
- **H4. `blueprints/jobs.py:59 / worker/tasks.py:24` — payload 화이트리스트 부재 (A03-3)**. `submit_job_task.apply_async(kwargs=payload)` 가 사용자 입력을 그대로 Celery kwargs 로 전달. payload 가 `{"foo":"bar"}` 같이 unknown 키면 TypeError → 500 (DoS 표면). pydantic 스키마 또는 `extra="forbid"` 검증 필요.
- **H5. `utils/emit_timing.py` — `X-Perf-Client: test` 헤더 검증 미구현**. ADR §5.4.3 다층 가드 (b) 위반. 현 구현은 `strip_internal_keys` 가 무조건 `_` prefix 키 strip → **카맥의 `sse_emit_to_receive_seconds` 측정 훅 동작 불능** (T6 인터페이스 회귀). 응답 누설은 우연히 0 이지만 ADR Patch 2 의 헤더 정확 일치 검증 부재로 카맥 T6 사양 미달.
- **H6. 정적분석 게이트 미통과 (ruff 66 + pyright 17)**. review-log §0.1 게이트상 0 error 필수.
- **H7. 의존성 audit 미실행 (pip-audit 미설치)**. A06-1 게이트 미실행 = 자동 게이트 누락.
- **H8. `test_cancel_already_canceled_job_returns_409` — `INVALID_TRANSITION` 코드 필드 미검증**. regression.md SM-1·SM-2 가 CRITICAL 인데 응답 본문 검증이 status code 만. 본 코드 (jobs.py:115) 자체가 envelope·code 둘 다 누락 → 테스트가 통과해도 회귀 검출 불가.

#### MEDIUM (코멘트 후 머지 허용 — 본 PR 내 수정 권장)

- **M1. `models/job.py:45 to_dict()` — `idempotency_key` 응답 노출**. ADR §5.2 표준 `job` 객체 명세에 미포함. 사용자 본인 키이지만 응답 스펙 불일치. 시나리오 5 의 server-generated key 회신 요구로 인해 idempotencyKey 필드명·노출 위치는 별도 확정 필요.
- **M2. `services/job.py` retry 분기 — `job.retried` 이벤트 발행 미구현**. jobs.py L121-138 흐름에서 `{jobId:F, newJobId:N}` 이벤트 발행 없음. 시나리오 5 step 4 회귀.
- **M3. `test_retry_failed_job_returns_new_job` — `retried_to_job_id` 검증 누락**. 원본 행 F.retried_to_job_id = N.id 검증 안 함. 시나리오 5 step 3 회귀.
- **M4. `/api/events/jobs/:id` cross-user IDOR 테스트 부재**. A01-3 (CRITICAL 게이트) 검증 누락. 코드는 검증함 (`events.py:83`) 이지만 테스트 부재.
- **M5. PATCH cancel/retry cross-user 시도 테스트 부재**. A01-2 검증 누락.
- **M6. `test_get_other_users_job_returns_404` — 응답 시간 분산 미검증**. A01-8 timing-and-message (분산 ≤ 30%) 검증 누락.
- **M7. 워커→DB 흐름 미구현**. `dummy_sleep` 가 `jobs.status` 를 갱신하는 경로 없음. **Phase 1 범위 모호** — Phase 2 인지 마크 회신 필요. 시나리오 2 풀 경로 통과 불가.
- **M8. error 마스킹 미구현**. 시나리오 3 의 `error.message` ≤200자 + stack/secret 부재. 워커 실패 경로가 없으므로 미구현. **Phase 2 가능**.
- **M9. `worker/tasks.py:26` — seconds type 검증 부재**. 비 int 입력 시 TypeError → 500. 간접 DoS.
- **M10. `Job.query.get()` deprecation (15 warnings)**. SQLAlchemy 2.0 `Session.get()` 권장.
- **M11. `blueprints/jobs.py:141 unknown action` — 회귀 테스트 부재**. 1줄 추가 권장.

#### LOW

- **L1. `blueprints/jobs.py:11` — unused import `datetime, timezone`**. ruff F401.
- **L2. `tests/conftest.py:42` — `_ext._redis_client = fake_redis` 직접 변수 교체**. 결합 위험, 향후 fixture 로 격리 권장.

#### 정합성 — 통과 확인 (강점)

- `validate_csrf_token` (csrf.py:20) — `secrets.compare_digest` 타이밍 안전 비교 ✅ (A02-7)
- `argon2id` (services/auth — 별도 검증) — 본 PR 영향 없음
- IDOR 차단 코드 `Job.query.filter_by(id=..., user_id=...)` (jobs.py:95, 109; events.py:83) ✅ — 테스트가 일부 누락된 것만 보정 필요
- Idempotency-Key 헤더 누락 422 ✅ + 중복 키 200 동일 job 반환 ✅
- `INVALID_TRANSITION` 코드 (jobs.py:123, 125) — Patch 3 정합 ✅ (단, envelope 형식만 H3 와 합쳐 수정)
- Celery `acks_late=True` (worker/tasks.py:22) — ADR §3.4 정합 ✅
- `task_serializer='json'` 가정 (별도 확인 필요) — pickle/marshal 부재 — A08-6 정합 추정

#### 후속 (마크 측 조치)

1. **즉시 CRITICAL/HIGH 13건 동일 PR 내 수정** — 본 코멘트 등급 표기 그대로.
2. **인터페이스 변경 (H1)** — `action=cancel` 유지 원하면 네이선과 ADR Patch 협의 후 라벨 추가. 권장은 ADR §5.1 의 `{status:"canceled"}` 원형 복귀.
3. **재제출 시 `ruff check --fix` + `pyright src` + `pip-audit` 실행 결과 PR 본문 포함**.
4. **마크 회신 대기 항목 Q-A1/A2/A4/S1/S2/S3 — 본 PR 차단 사유와 별도이나 Phase 2 진입 전 필수**.

#### CTO 알림

C1·C2·C5 CRITICAL 3건은 ADR §5.4 / §1.2 / §5.4.3 의 핵심 인터페이스 회귀. team-send 제임스 동시 통지.


---

## 2. 영역별 게이트 적용 표

| 변경 영역 | 보안 audit 필수 절 | 회귀 필수 절 | E2E 필수 시나리오 | 비고 |
|---|---|---|---|---|
| 인증·세션 (`/auth/*`, `app/auth/*`) | A01·A02·A07 | §2·§4 + §1 SM-1/SM-2 | #1 | 쿠키 파싱은 Flask 기본 (첫 번째 sid). [regression.md](regression.md) AUTH-4 |
| 작업 제출·조회 (`/api/jobs`, `app/jobs/*`) | A01·A03·A08 | §1·§6 | #2·#6 | retry 는 `failed`/`canceled` 만 (Q-R1, ADR-001 Patch 3 대기) |
| 워커·Celery (`celery_app.py`, `app/worker/*`) | A03·A08·A09 | §1 SM-5/SM-6 | #2·#3·#4 | |
| SSE (`/api/events/*`, `app/events/*`) | A01·A05·A09 | §5 + §7 LOAD-3 | #2·#7·#8 | |
| 마이그레이션 (`migrations/*`) | A01·A08 | §1 (스키마 정합) | (해당 영역) | |
| UI (`web/*`, `src/components/*`) | A03·A09 + 디자인 게이트 | — | 디자인 a11y 게이트 | |
| 인프라 (`docker-compose.yml`, `.env.example`) | A05 (R-006) | — | — | |

---

## 3. 반복 이슈 트래커

> 동일 유형 위반이 PR 별로 반복되면 본 섹션에 누적. 임계치(3회) 초과 시 [security-audit.md](security-audit.md) 또는 코드 컨벤션 문서 강화 PR 발행.

| 유형 | 누적 | 마지막 발견 PR | 후속 |
|---|---|---|---|
| 응답 envelope 누락 (ADR §5.5 `{error:{code,message}}` 미준수) | 1 | #3 | 3회 누적 시 docs/qa/security-audit.md 에 envelope 체크리스트 추가 |
| 이벤트 카탈로그 회귀 (이름·페이로드 ADR §5.4 불일치) | 1 | #3 | 3회 누적 시 publish_job_event 호출부에 lint 룰 도입 |
| 정적분석 게이트 미통과 (ruff/pyright) | 1 | #3 | PR 제출 전 마크 자가 점검 의무화 |
| Idempotency lock race (existing None 시 진행) | 1 | #3 | 코드 컨벤션에 race-safe 패턴 추가 |

---

## 4. 주기적 검증 로그

> [_team-workflow.md](../../roles/_team-workflow.md) §7.2 정민 주기적 검증 산출물. 별도 행으로 누적.

### 4.1 주간 dead code · 의존성 CVE 스캔

| 주차 | 실행일 | dead code (knip/ts-prune) | CVE (pip-audit/npm audit) | 조치 |
|---|---|---|---|---|
| 2026-W21 | _예정 2026-05-26_ | — | — | — |

### 4.2 주간 커버리지 추이

| 주차 | 단위 (라인%) | 통합 (라인%) | E2E 통과율 | 마크에게 보강 요청 |
|---|---|---|---|---|
| 2026-W21 | _대기_ | _대기_ | _대기_ | — |

### 4.3 주간 회귀 batch 결과 (regression.md §회귀 게이트 실행 매트릭스)

| 주차 | 실행일 | §1~§6 결과 | §7 LOAD 결과 | 회귀 발견 |
|---|---|---|---|---|
| 2026-W21 | _예정_ | — | — | — |

---

## 5. 첫 PR 수신 전 셋업 체크리스트

마크의 첫 PR 도착 전에 정민이 사전 완료해야 할 항목.

- [x] [scenarios.md](scenarios.md) 시나리오 8건 명세 — 2026-05-19 완료
- [x] [security-audit.md](security-audit.md) OWASP A01~A10 — 2026-05-19 완료
- [x] [regression.md](regression.md) 회귀 매트릭스 — 2026-05-19 완료
- [x] CTO 답변 4건 (Q-A3, Q-R1, Q-R2, Q-R3) 명세 반영 — 2026-05-19 완료 ([inspection-T5-jungmin.md](inspection-T5-jungmin.md))
- [x] 카맥과 LOAD-1/2 도구 통일 합의 — **locust 확정** (Q-R3, 2026-05-19)
- [ ] 마크 회신 6건 수신 — Q-A1 / Q-A2 / Q-A4 / Q-S1 / Q-S2 / Q-S3 (제임스가 마크에 별도 위임)
- [ ] ADR-001 Patch 3 머지 (네이선) — `succeeded` retry 불가 명시. SM-4 게이트 HIGH 격상 의존
- [ ] CI 파이프라인 게이트 등록 (마크 협업, 첫 PR 일정 맞춤) — 대기

---

## 6. 운영 메모

- 본 로그는 머지 후에도 절대 행 삭제하지 않음. 잘못된 행은 line-through (`~~...~~`) 처리 후 사유를 비고에 적는다.
- CRITICAL 발견 시 정민은 즉시 `team-send 제임스 "[CRITICAL] PR #__ ..."` 보고. 마크에게 차단 코멘트는 동시에 송신.
- MEDIUM/LOW 후속은 Jira Sub-task 생성 후 비고 컬럼에 키 기록.
- 분기 검토 — 반복 이슈 트래커가 3회 이상인 유형은 분기 회고에 안건으로 올린다.
