# PR 머지 게이트 리뷰 로그

- 최종 갱신: 2026-05-19 by 정민
- 상위: [T5](../tasks/T5-qa-jungmin.md), [scenarios.md](scenarios.md), [security-audit.md](security-audit.md), [regression.md](regression.md)
- 운영자: 정민. 마크의 모든 PR 은 본 로그의 게이트를 통과해야 머지.

## 0. 게이트 절차

> **본 프로젝트 (taskq) 운영 컨텍스트** (2026-05-19, 제임스 공지).
> - origin: `https://github.com/jinyu74/claude-team.git`
> - 통합 브랜치: `develop/taskq/v0.1.0`
> - 태스크 브랜치 명명: `develop/taskq/<slug>` (Jira 키 형식 아님)
> - **Jira 면제** — 차단 사유·후속 추적의 SSOT 는 본 `review-log.md` (행 표 + 반복 이슈 트래커). 외부 이슈 시스템 참조 없음.
> - PR 흐름: `develop/taskq/<slug>` → `develop/taskq/v0.1.0` 마다 본 게이트 가동. v0.1.0 → main 머지 PR 은 별도 요청 시.
> - **PR 본문 의무**: 첫 줄 `slug: <name>` (CTO 추인 2026-05-19). 누락 시 review-log 행 슬러그 컬럼이 "(미상)" 으로 기록되어 추후 보강 요구로 이어짐.

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

| 일자 | PR # | 제목 (요약) | 브랜치 (`develop/taskq/<slug>`) | CI 그린 | 보안 audit | 회귀 | E2E 시나리오 | CRITICAL | HIGH | MEDIUM | LOW | 결론 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-19 | #3 | jobs API + worker Phase 1 | _(슬러그 미상 — 마크 재제출 시 명시)_ → `develop/taskq/v0.1.0` | ✅ 58 passed, 82.00% cov / ❌ ruff 66 / ❌ pyright 17 / ❌ pip-audit 미설치 | ❌ A01·A03·A08 위반 다수 | ❌ §1 SM-1/2 envelope 위반, §6 IDEM lock race 누설 | ❌ #2 이벤트 카탈로그 회귀, #6 멱등 race 미수정 | **5** | **8** | **11** | **2** | **차단** | [상세](#pr-3-상세) |
| 2026-05-19 | #1 | H5 픽스 — `sse_emit_to_receive_seconds` 라벨 `[channel, client_type]` 추가 + `X-Perf-Client: test` 정확 일치 가드 | `develop/taskq/perf-h5-metric-labels` → `develop/taskq/v0.1.0` | ✅ 59 passed, 81.04% cov / ✅ ruff 0 / ✅ pyright 0 | ✅ A01-9 5층 가드 + 4 환경 매트릭스 충족 (운영/평범/임의헤더/test 모두 정상) | — (영역 외) | #2 `_emit_at` strip 정합 ✅ | 0 | 0 | **1** | **2** | **허용** | [상세](#pr-1-상세) |

### 행 작성 규칙

- "결론" 컬럼은 `허용` / `보류` / `차단` 3종.
- "비고" 컬럼에는 차단 사유 또는 후속 슬러그 (Jira 면제 — 외부 키 없음).
- "브랜치" 컬럼은 `develop/taskq/<slug>` 형식. PR 본문에 명시 안 됐으면 마크에게 재제출 시 보강 요청.
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
  - **2026-05-19 진단 보정** (CTO 인정, PR #1 게이트 시 확인). 위 라벨 "헤더 검증 미구현" 은 부수 원인만 짚었고, **결정적 원인은 `utils/metrics.py:47-52` 의 `sse_emit_to_receive_seconds` 히스토그램 라벨 `[channel, client_type]` 부재** → 카맥 P-02/P-03 PromQL 쿼리 (`{channel="user|job", client_type="test"}`) 가 time-series 식별 불가. PR #1 (카맥) 가 (a) 라벨 추가 + (b) 헤더 정확 일치 검증 둘 다 동시 해결. 향후 진단 시 ADR §7.2 메트릭 카탈로그까지 cross-check 후 라벨화. 라인 인용 명시 의무 (CTO 권고).
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

> **수정 순서.** CTO 가 [inspection-PR3-gate.md](inspection-PR3-gate.md) §4그룹 우선순위 (A 인터페이스 정합 / B 이벤트 흐름+측정 훅 / C 보안·정합 / D 자동 게이트) 로 분류해 마크에 발송. 같은 모듈을 두 번 건드리지 않도록 그룹 단위 PR 또는 commit. 네이선·카맥에는 H1·H5 별도 통지 완료.

1. **즉시 CRITICAL/HIGH 13건 동일 PR 내 수정** — 본 코멘트 등급 표기 그대로.
2. **인터페이스 변경 (H1)** — `action=cancel` 유지 원하면 네이선과 ADR Patch 협의 후 라벨 추가. 권장은 ADR §5.1 의 `{status:"canceled"}` 원형 복귀.
3. **재제출 시 `ruff check --fix` + `pyright src` + `pip-audit` 실행 결과 PR 본문 포함**.
4. **마크 회신 대기 항목 Q-A1/A2/A4/S1/S2/S3 — 본 PR 차단 사유와 별도이나 Phase 2 진입 전 필수**.
5. **PR 본문에 브랜치 슬러그 명시** — 본 PR 의 head 브랜치 `develop/taskq/<slug>` 의 슬러그 값을 본문 첫 줄에 적어 review-log 갱신 가능하게.

#### CTO 알림

C1·C2·C5 CRITICAL 3건은 ADR §5.4 / §1.2 / §5.4.3 의 핵심 인터페이스 회귀. team-send 제임스 동시 통지.

---

### PR #1 상세

**결론.** **머지 허용** (CRITICAL 0 / HIGH 0 / MEDIUM 1 / LOW 2). 카맥의 H5 픽스. ADR §7.2 메트릭 라벨 + §5.4.3 다층 가드 정합 충족. PR #3 의 H5 항목 보정 반영 완료.

**자동 게이트.**
- 단위/통합 ✅ 59 passed (카맥 보고 59 일치)
- 커버리지 ✅ 81.04% (카맥 보고 81.04% 일치)
- 정적분석 ✅ ruff 0 errors (변경 4 파일) / pyright 0 errors (변경 3 파일)
- 의존성 audit — PR #3 와 동일 사유로 pip-audit 미설치 (영역 외, 본 PR 차단 사유 아님)

**ADR §5.4.3 다층 가드 5층 매칭.**

| 가드 | 위치 | 충족 |
|---|---|---|
| 1. 워커 부착 (`ENABLE_EMIT_AT=true` 시에만) | `utils/emit_timing.py:5-12` | ✅ 변경 없음 |
| 2. 클라이언트 식별 (`X-Perf-Client: test` **정확 일치**) | `blueprints/events.py:70` (`request.headers.get("X-Perf-Client") == "test"`) | ✅ 신규 |
| 3. 직렬화 strip (`_` prefix) | `utils/emit_timing.py:35-42` | ✅ `expose_emit_at` 분기 신규 |
| 4. 로그 금지 | 변경 3 파일에 logger 호출 없음. `services/sse.py:50` 의 `publish_job_event` 도 로그 미경유 | ✅ |
| 5. 노출 AND 조건 | `blueprints/events.py:71` (`expose_emit_at = ENABLE_EMIT_AT and is_test_client`) | ✅ |

**A01-9 4 환경 매트릭스 검증** (security-audit.md A09.a 보강 표).

| 환경 | `ENABLE_EMIT_AT` | `X-Perf-Client` | 코드 흐름 | 응답에 `_emit_at` |
|---|---|---|---|---|
| 운영 | false (미설정) | 무관 | `maybe_add_emit_at` noop → 페이로드에 키 없음 | ❌ 부재 ✅ |
| 테스트 + 평범 클라이언트 | true | 헤더 없음 | `is_test_client = (None == "test") = False` → `expose_emit_at = True and False = False` → strip | ❌ 부재 ✅ |
| 테스트 + 임의 헤더 | true | `prod` (정확 미일치) | `is_test_client = ("prod" == "test") = False` → strip | ❌ 부재 ✅ |
| 테스트 + 테스트 클라이언트 | true | `test` | `is_test_client = True` → `expose_emit_at = True` → `result[k] = v` | ✅ 노출 ✅ |

**ADR §7.2 메트릭 카탈로그 정합** — `sse_emit_to_receive_seconds` 라벨 `[channel, client_type]`:
- `utils/metrics.py:50` 정확 일치 ✅
- 라벨 값 도메인 — `channel` ∈ {"user", "job"} (events.py L106·L117 명시), `client_type` = "test" 만 사용 (테스트 빌드 한정, observe 호출 위치 emit_timing.py L29-31). 카디널리티 = 2 × 1 = 2 time-series. 폭발 위험 0 ✅
- 카맥 P-02/P-03 PromQL 쿼리 (`{channel="user|job", client_type="test"}`) 가 본 PR 머지 후 time-series 식별 가능 ✅

**발견 사항.**

#### MEDIUM (1건)

- **M1. `tests/unit/test_emit_timing.py` — `expose_emit_at=True` 노출 경로 단위 테스트 부재**. 본 PR 의 핵심 신규 분기 (emit_timing.py:38-39 `result[k] = v` for `_emit_at`) 가 커버리지 미커버 (`emit_timing.py 87% — Missing 32-33, 39`). `expose_emit_at=True` + `is_test_client=True` 시 `_emit_at` 가 결과 dict 에 살아남는지 1줄 assert 추가 권장. 본 PR 내 보정 또는 후속 1줄 PR.

#### LOW (2건)

- **L1. `utils/emit_timing.py:32-33` — `try/except (ValueError, TypeError): pass`**. silent failure 패턴. `_emit_at` 가 손상 타입일 때 측정만 누락 — 응답·보안 영향 없음. 단, 동일 패턴이 다른 영역에 확산되면 [silent-failure-hunter] 회귀 위험. 본 케이스에서는 측정 무시가 합리적 (정상 운영에서 발생 안 함). 메모만.
- **L2. `blueprints/events.py:114` — `{"error": "Not found"}` envelope 위반 (PR #3 H3 잔존)**. 본 PR 의 직접 변경은 아니나 같은 파일에 잔존. 마크 PR #3 재제출 시 일괄 처리. 본 PR 차단 사유 아님.

**정합성 — 통과 확인 (강점).**

- 라벨 도메인 = ADR §7.2 카탈로그 정확 일치 (`channel`/`client_type`) — 본 PR 의 핵심 픽스
- `X-Perf-Client: test` **정확 일치** (`== "test"`) — contains 우회 차단 ✅ (security-audit.md A01-9 4 환경 매트릭스의 "임의 헤더" 케이스 충족)
- AND 조건 (`ENABLE_EMIT_AT and is_test_client`) — events.py L71 단일 지점 ✅
- `expose_emit_at=False` 가 기본값 — fail-safe 설계 ✅
- 시그니처 변경 `strip_internal_keys` — caller (events.py:41) 가 4 인자 모두 전달 ✅. 단위 테스트 (test_emit_timing.py:50,67,80) 도 시그니처 정합 ✅
- 카디널리티 2 — A09 폭발 위험 0 ✅ (카맥 자가 점검 명시 일치)

#### 후속 (카맥 측 조치)

1. M1 1줄 단위 테스트 추가 (본 PR 내 또는 후속 1줄 PR — 정민 선호: 본 PR 내).
2. 머지 후 `load_tests/locustfile_sse_latency.py` 재실행 → P-02/P-03 PromQL 쿼리 시계열 복구 확인. 본 게이트 통과가 머지 트리거.

#### 정민 진단 보정 (CTO 추인)

PR #3 §H5 항목 본문 끝에 보정 한 줄 추가 (본 review-log 위쪽 §PR #3 상세 §HIGH H5 참조). 향후 메트릭/관측성 영역 진단 시 ADR §7.2 메트릭 카탈로그까지 cross-check 후 라벨화. 라인 인용 의무 (CTO 권고 2026-05-19).


---

## 2. 영역별 게이트 적용 표

> 본 표의 모든 PR 은 base = `develop/taskq/v0.1.0`, head = `develop/taskq/<slug>`. v0.1.0 → `main` 머지 PR 은 별도 릴리스 게이트.

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
>
> **3회 누적 자동 강화 권한 (2026-05-19 CTO 위임).** 임계치 도달 시 정민이 별도 승인 없이 강화 PR 을 발행한다. PR 본문에 `누적 3회 (PR #x·#y·#z)` 근거 표기 + 변경 후 본 트래커 행을 line-through 처리.

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
- [x] git origin·통합 브랜치 셋업 — `jinyu74/claude-team` + `develop/taskq/v0.1.0` (2026-05-19 13:54, 제임스 공지)
- [x] ADR-001 Patch 3 머지 (네이선) — `succeeded` retry 불가 명시. SM-4 HIGH 게이트 활성 (2026-05-19)
- [x] 첫 PR (#3) 머지 게이트 가동 — 차단 결론, review-log §PR #3 상세
- [ ] 마크 회신 6건 수신 — Q-A1 / Q-A2 / Q-A4 / Q-S1 / Q-S2 / Q-S3 (제임스가 마크에 별도 위임)
- [ ] 마크 PR #3 재제출 + CRITICAL/HIGH 13건 수정 — 대기 (4그룹 A/B/C/D 순서, [inspection-PR3-gate.md](inspection-PR3-gate.md) §4그룹 우선순위)
  - **추가 검증 항목**: **E1/E2 (네이선 발견)** 포함 (CTO 통지 2026-05-19 14:54). 정의는 재제출 PR 본문 또는 네이선 직접 send 도착 시 흡수. 정의 도착 전까지 본 행 보존.
- [ ] CI 파이프라인 게이트 등록 (마크 협업) — 대기

---

## 6. 운영 메모

- 본 로그는 머지 후에도 절대 행 삭제하지 않음. 잘못된 행은 line-through (`~~...~~`) 처리 후 사유를 비고에 적는다.
- CRITICAL 발견 시 정민은 즉시 `team-send 제임스 "[CRITICAL] PR #__ ..."` 보고. 마크에게 차단 코멘트는 동시에 송신.
- MEDIUM/LOW 후속은 Jira Sub-task 생성 후 비고 컬럼에 키 기록.
- 분기 검토 — 반복 이슈 트래커가 3회 이상인 유형은 분기 회고에 안건으로 올린다.
