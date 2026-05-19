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
> - **슬러그 PR 별 고유 — 동시 작업 금지** (CTO 추인 2026-05-19 15:09 / 우회 통합 사고 재발 방지). 동일 슬러그 브랜치는 한 PR 의 머지 완료 후에만 재사용. 사고 사례 — `develop/taskq/pr3-gate-fixes` 가 카맥 PR #2 와 마크 PR #3 작업에서 동시 사용되어 v0.1.0 머지 시 정민 미검증 fix(7fef3db) 흡수 (사후 게이트로 보정).
>
> **§8 게이트키퍼 운영 규칙 (5단계) — ADR-001 §8.1 SSOT** (정식 채택 2026-05-19 15:11, Patch 4). 네이선이 인터페이스 변경 PR 검증 시 적용. ①`interface-change` 라벨, ②§4·§5·§6 경로 휴리스틱, ③컨텍스트 라인 검증, ④SSOT 트레이스 (`docs/tasks/T*.md` ↔ `docs/qa/inspection-*.md` ↔ ADR-001), ⑤머지 직전 head SHA 일치 검증 (통과 코멘트에 검증 시점 SHA 명시). 1차 SSOT: [ADR-001 §8.1](../decisions/ADR-001-architecture.md). 본 review-log 는 2차 SSOT cross-reference. 검증 사례: PR #1 (gh pr comment 1), PR #2 (gh pr comment 2), PR #3 (gh pr comment 3 — head SHA 명시).

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
| 2026-05-19 | #3 | jobs API + worker Phase 1 | _(슬러그 미상 — 마크 재제출 시 명시)_ → `develop/taskq/v0.1.0` | ✅ 58 passed, 82.00% cov / ❌ ruff 66 / ❌ pyright 17 / ❌ pip-audit 미설치 | ❌ A01·A03·A08 위반 다수 | ❌ §1 SM-1/2 envelope 위반, §6 IDEM lock race 누설 | ❌ #2 이벤트 카탈로그 회귀, #6 멱등 race 미수정 | **5** | **8** | **11** | **2** | **차단** | [상세](#pr-3-상세) / **사후 게이트 미통과** (HIGH 3 잔존, 2026-05-19 15:09 ~ 15:14 CTO 결재 대기) |
| 2026-05-19 | — | 사후 게이트 (7fef3db 우회 통합 검증) | 검증 대상 SHA `7fef3db` (v0.1.0 origin HEAD) | ✅ 60 passed, 81.34% cov / ✅ ruff 0 / ✅ pyright 0 / ⚠️ pip-audit 미설치 (영역 외) | C1-C5 ✅ 해결 / H1 ✅ / H2 ✅ / H3 ⚠️ 부분 잔존 / H4 ✅ / H5 ✅(PR #1) / H8 ⚠️ 부분 잔존 / E2 ✅ | SM-4 ✅ jobs.py L142 / SM-1·2 ⚠️ 테스트 미커버 | #2 이벤트 카탈로그 ✅ / 채널 분리 ✅ / 1s throttle ✅ | 0 | **3** | 1 | 0 | **미통과 (사후)** | **CTO 결재 (a) hotfix PR 채택** (15:19, MEDIUM event_id 포함 4건 확장) — [상세](#pr-3-사후-게이트-상세) |
| 2026-05-19 | #4 | hotfix H3-a/H3-b/MEDIUM(2) + H8 | `develop/taskq/hotfix-h3-envelope` → `develop/taskq/v0.1.0` (head SHA `3b84acf1ff540ab2b4e630ada5b0e13968927634`) | ✅ 60 passed, 81.34% cov / ✅ ruff 0 / ✅ pyright 0 / ✅ pip-audit clean (마크 자가 보고) | ✅ A01·A05 정합 (UNAUTHENTICATED/NOT_FOUND envelope) | ✅ SM-1·2 회귀 보강 가능 (H8 test L231 `code == "INVALID_TRANSITION"` assert 추가) | ✅ 시나리오 1 step 3·7 envelope 정합 | 0 | 0 | 0 | 0 | **허용 (PR #4 범위)** | ⑤ head SHA 명시. **정민 진단 보정 — auth.py 3건 envelope 잔존 신규 발견** (PR #4 범위 외) → [상세](#pr-4-상세) |
| ~~2026-05-19~~ | ~~#5 (1차)~~ | ~~auth-envelope hotfix — H3-c/H3-d/H3-e~~ | ~~head `94436387`~~ | — | — | — | — | 0 | 0 | 0 | 0 | ~~허용~~ | **⑤ 룰 작동 — force-push 후 head 변경 → 재검증으로 회귀 발견 → 통과 무효** ([§PR #5 상세](#pr-5-상세)) |
| 2026-05-19 | #5 (재검증) | auth-envelope hotfix — H3-c/H3-d/H3-e | `develop/taskq/hotfix-auth-envelope` → `develop/taskq/v0.1.0` (force-push head SHA `9b4a2631a3c833eaadeb02f88b5255381195445f`, 이전 head `94436387` 무효) | ✅ 60 passed, 81.39% cov / ✅ ruff 0 (자동 게이트 통과하나 envelope 회귀를 잡지 못한 한계) | ❌ A07-2 부분 회귀 — session.py·events.py flat envelope 환원 | — | ❌ 시나리오 1 step 7 + 시나리오 7 envelope 회귀 | 0 | **2** | 0 | 0 | **재검증 실패 (회귀)** | base 가 PR #4 (3b84acf) 머지 이전 d7b59d1 에서 분기 → PR #4 envelope 회복 회귀. 마크 rebase 요청 — [상세](#pr-5-상세) |
| 2026-05-19 | #6 | hotfix v2 — H3-c/H3-d/H3-e (auth.py) + envelope 단위 테스트 5건 + (흡수) docs review-log + ADR §8.1 | `develop/taskq/hotfix-auth-envelope-v2` → `develop/taskq/v0.1.0` (head SHA `9a8484b7b172d9f566b2c006c0805c0deade5f33`) | ✅ 60 passed, 81.39% cov / ✅ ruff 0 / ✅ pip-audit clean | ✅ A07-2 사용자 열거 방어 정합 | — | ✅ 시나리오 1 step 3·7 envelope 정합 + 단위 테스트 5건 회귀 검증 | 0 | 0 | 0 | **1** | **허용 + 머지 완료** | **3축 강화 게이트 통과** (① ancestor ✅ / envelope 6 라우트 ✅ / 단위 테스트 5건 ✅). ⑤ head SHA 일치 후 머지 (CTO 결재 (b) 본문 명시 후 머지, 16:04). v0.1.0 새 HEAD = 9a8484b (merge 2932dad). [상세](#pr-6-상세) |
| 2026-05-19 | #1 | H5 픽스 — `sse_emit_to_receive_seconds` 라벨 `[channel, client_type]` 추가 + `X-Perf-Client: test` 정확 일치 가드 | `develop/taskq/perf-h5-metric-labels` → `develop/taskq/v0.1.0` | ✅ 59 passed, 81.04% cov / ✅ ruff 0 / ✅ pyright 0 | ✅ A01-9 5층 가드 + 4 환경 매트릭스 충족 (운영/평범/임의헤더/test 모두 정상) | — (영역 외) | #2 `_emit_at` strip 정합 ✅ | 0 | 0 | **1** | **2** | **허용** | [상세](#pr-1-상세) |
| 2026-05-19 | #2 | E1 픽스 (`_emit_at` float → `{iso, monotonic_ns}` dict) + M1 후속 (`expose_emit_at=True` 단위 테스트) | `develop/taskq/pr3-gate-fixes` → `develop/taskq/v0.1.0` (※ 슬러그 메타 — CTO 별도 권고) | ✅ 60 passed, 81.34% cov / ✅ ruff 0 (src+tests) / ✅ pyright 0 / ⚠️ ruff 4 (load_tests 외부) | ✅ A01-9 4 환경 매트릭스 dict 포맷에서도 유지 (가드 약화 없음) | — (영역 외, SSE-1 무관) | #2 측정 보조 ✅ | 0 | 0 | 0 | **3** | **허용** | [상세](#pr-2-상세) |

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

### PR #3 사후 게이트 상세

**배경.** 2026-05-19 15:09 CTO 제임스 긴급 통지 — 카맥 PR #2 와 마크 PR #3 작업이 동일 슬러그 `develop/taskq/pr3-gate-fixes` 사용. 마크가 카맥 PR 브랜치에 15:02:40 직접 push 한 `7fef3db fix(jobs): PR #3 gate fixes — C1-C5, H1-H8, E1-E2` 가 카맥 PR #2 머지 시점에 v0.1.0 으로 우회 통합. 정민 PR #2 게이트(C0/H0/M0/L3)는 head=`5330865` 시점만 검증, `7fef3db` 는 미검증 상태로 머지됨.

**검증 시점.** 2026-05-19 15:13 (정민이 detached HEAD `7fef3db` 체크아웃 후 정밀 검증).
**검증 시점 head SHA.** `7fef3db` (origin/develop/taskq/v0.1.0 HEAD, 본 사후 게이트 시점).

**결론.** **사후 게이트 미통과** (CRITICAL 0 / **HIGH 3 잔존** / MEDIUM 1 / LOW 0). hotfix PR 또는 v0.1.0 revert 권고 — CTO 결재 요청.

**자동 게이트.**
- 단위/통합 ✅ 60 passed
- 커버리지 ✅ TOTAL 81.34%
- 정적분석 ✅ ruff 0 (src + tests) / pyright 0 (src 전 영역)
- 의존성 ⚠️ pip-audit 미설치 (마크 회신 Q-S2 수신 — `.audit-ignore` PR 방식 채택, 별도 인프라 PR 에서 설치 예정. 본 사후 게이트 미통과 사유 아님)

**해결 확인 (CRITICAL 5 + HIGH 8 중 10건).**

| ID | 해결 위치 | 검증 결과 |
|---|---|---|
| C1 페이로드 전체 `to_dict()` 노출 | `services/job.py:13-21 _EVENT_PAYLOAD_KEYS` 카탈로그 + L40-44 `_event_payload()` cherry-pick | ✅ ADR §5.4 카탈로그별 키만 발행 (`job.submitted`: 4 키, `job.started`: 3 키 등) |
| C2 `job_events` INSERT 부재 | `services/job.py:47-54 _record_event()` 가 publish 후 INSERT + commit | ✅ event_ulid 동기화 ✅ |
| C3 `job.created` 이름 회귀 | `services/job.py:77 event_type = "job.submitted"` | ✅ |
| C4 `job.running` 이름 회귀 | `services/job.py:23-29 _STATUS_TO_EVENT` 매핑 (running → `job.started`) | ✅ |
| C5 양채널 동일 발행 + throttle 부재 | `services/sse.py:17-22 _USER_ONLY_EVENTS` / `_JOB_ONLY_EVENTS` 분리 + L59-65 `job.progress` user 1s throttle (Redis `SET NX EX 1`) | ✅ 채널 분리·throttle 모두 정합 |
| H1 PATCH cancel 인터페이스 | `blueprints/jobs.py:129 if data.get("status") == "canceled"` (ADR §5.1 원형 복귀) | ✅ |
| H2 Idempotency lock race | `services/job.py:65-71 ConflictError raise` + `jobs.py:68-72 409 IDEMPOTENCY_CONFLICT` catch | ✅ PG UNIQUE 위반 직전 차단, 5xx 누수 0 |
| H4 payload 화이트리스트 | `jobs.py:23 _TASK_KWARGS_WHITELIST = frozenset(["seconds", "fail_prob"])` + L77, L155-157 filter | ✅ 사용자 unknown 키 차단 |
| H5 (이미 PR #1·#2) | `utils/emit_timing.py` + `metrics.py` | ✅ |
| **E2 `sse_messages_sent_total` 라벨명** | `utils/metrics.py:44 ["channel", "event"]` (ADR §7.2 카탈로그 일치) + `events.py:48, 78 .labels(channel=..., event=...)` | ✅ |

**잔존 발견.**

#### HIGH (3건 — 사후 미통과 사유)

- **H3-a (잔존). `middleware/session.py:26` — `return jsonify({"error": "Unauthorized"}), 401`**. ADR §5.5 envelope `{"error":{"code":"...","message":"..."}}` 미준수. `code` 필드 부재. 마크 fix 가 `blueprints/jobs.py` 의 envelope 는 `_err` 헬퍼로 일관 처리했으나 middleware 영역 누락. 시나리오 1 step 7 의 `error.code == "UNAUTHENTICATED"` 검증 불통과.
- **H3-b (잔존). `blueprints/events.py:114` — `return {"error": "Not found"}, 404`**. 동일 envelope 미준수. `NOT_FOUND` code 필드 부재. 작업 상세 SSE 의 IDOR 경로 응답. A01-3 (CRITICAL 게이트) 의 응답 본문 검증 + 시나리오 7 cross-user IDOR 검증 시 envelope 불일치로 실패.
- **H8 (부분 잔존). `tests/integration/test_job_endpoints.py:209-231 test_cancel_already_canceled_job_returns_409`**. `assert resp.status_code == 409` 만 검증, `resp.get_json()["error"]["code"] == "INVALID_TRANSITION"` 미검증. regression.md SM-1·SM-2 가 CRITICAL 인데 회귀 검출 불가 (코드는 jobs.py:132 에서 정상 응답하지만 테스트가 회귀를 못 잡음). 참고로 retry 케이스 (L291, L304) 는 code 필드 검증 ✅.

#### MEDIUM (1건)

- **M-NEW. `services/job.py:52` — `event_id = uuid.uuid4().int >> 65`**. SQLite BIGINT PRIMARY KEY 가 ROWID alias 안 됨 → 명시 INSERT. PG 운영에서는 `BIGSERIAL` 시퀀스가 자동 부여하므로 명시 ID 부여 시 시퀀스 갱신 안 됨 → 후속 INSERT 가 LOW value 시퀀스로 시도 → UNIQUE 위반 위험. SQLite 테스트는 통과, PG 통합 테스트 도입 시 회귀 가능. 시범 환경 (PG) 진입 전 보강 권장.

#### 정합성 — 통과 확인 (강점)

- 마크 fix 가 13건 중 10건을 정확히 해결 — 4그룹 A/B/C/D 우선순위에 충실
- C1 의 `_EVENT_PAYLOAD_KEYS` 카탈로그 + `_event_payload()` cherry-pick — ADR §5.4 카탈로그 SSOT 와 1:1 정합
- C5 의 `_USER_ONLY_EVENTS` / `_JOB_ONLY_EVENTS` frozenset + `job.progress` 분기 — 채널 분리 + 1s throttle 정확
- H2 의 `ConflictError` 명시 예외 — silent 분기 진행 (PR #3 원본) 보다 명확한 경계
- H4 의 `_TASK_KWARGS_WHITELIST` — submit·retry 양 경로 모두 적용
- E2 의 `sse_messages_sent_total` 라벨명 + ADR §7.2 카탈로그 일치 — backfill 도 동일 라벨 패턴

#### CTO 결재 요청 — 다음 단계 분기

| 옵션 | 설명 | 정민 권고 | CTO 결재 |
|---|---|---|---|
| (a) hotfix PR | `develop/taskq/hotfix-h3-envelope` 새 슬러그로 H3-a, H3-b, H8 3건 한 PR. 단순 envelope 헬퍼 적용 + 테스트 assert 1줄 추가 | **권장** — 변경 면적 작음, 동일 게이트 재가동 즉시 가능 | **✅ 채택 (2026-05-19 15:19)** — MEDIUM event_id 도 동일 PR 에 편입하여 4건 확장. 사고 후 사후 정합 부분 운영 인정 |
| (b) v0.1.0 revert | `git revert 7fef3db` 후 마크 새 PR 요구 | 비권장 — 해결 10건이 함께 폐기됨 | 기각 |
| (c) 사후 정합 인정 | HIGH 3 잔존 무시하고 통과 처리 | 비권장 — 시나리오 1·7 회귀 + A01-3 정합 위반 직접 영향 | 기각 |

**거버넌스 강화 (이미 §0 박스 반영).**
- 슬러그 PR 별 고유·동시 작업 금지 — 본 사고 재발 방지.
- ADR-001 §8.1 ⑤ 머지 직전 head SHA 일치 검증 — 통과 코멘트 시점 SHA 와 머지 SHA 불일치 시 통과 무효 + 재검증 요구 (네이선 룰).

#### 진단 자가 규칙 (PR #3 사후 게이트 → PR #1 H5 보정에 이은 두 번째 자율 보강)

- 인터페이스 정합 점검 시 jobs.py 같은 진입점만이 아니라 **응답 직렬화 경로 전체** (middleware·events·blueprints) 를 envelope 일관 grep 한 후 통과 코멘트. `grep -nE '"error"\s*:' src/{middleware,blueprints}/**/*.py` 같은 단순 스크립트로 1초.

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

### PR #2 상세

**결론.** **머지 허용** (CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 3). 카맥의 E1 (`_emit_at` float → `{iso, monotonic_ns}` dict 포맷 정합) + M1 후속 (expose_emit_at=True 단위 테스트). ADR §5.4.3 SSOT 포맷 정합, A01-9 5층 가드 dict 포맷에서도 유지.

**자동 게이트.**
- 단위/통합 ✅ 60 passed (+1 vs PR #1 머지 후 59 — M1 신규 테스트 1건, `test_expose_emit_at_included_when_flag_true`)
- 커버리지 ✅ 81.34% (카맥 보고 81.34% 일치). `emit_timing.py 93% (Missing 39-40)` — silent except 분기 미커버 (LOW)
- 정적분석 ✅ ruff 0 (`src` + `tests`) / pyright 0 (운영 영역)
- 정적분석 ⚠️ ruff 4 (`load_tests/locustfile_sse_latency.py`) — F401×1·I001×1·S110×1·S311×1. **운영 코드 영역 외** (load_tests/ 는 review-log §0.1 `ruff src tests` 게이트 범위 밖), 차단 사유 아님

**ADR §5.4.3 포맷 정합 검증.**

| 항목 | ADR §5.4.3 명세 | PR #2 구현 | 정합 |
|---|---|---|---|
| `_emit_at` 형식 | dict `{iso, monotonic_ns}` | `maybe_add_emit_at` L13-14: `{"iso": datetime.now(UTC).isoformat(), "monotonic_ns": time.monotonic_ns()}` | ✅ dict 키 2종 |
| `iso` 필드 | "2026-05-19T13:30:01.123456Z" (예시) | `datetime.now(UTC).isoformat()` 출력 → `"...+00:00"` 형식 | ⚠️ 표기 차 (운영 영향 없음 — locustfile L50 `replace("Z","+00:00")` defensive 처리) |
| `monotonic_ns` 필드 | 단조 시계 ns 정수 | `time.monotonic_ns()` | ✅ |
| 계산식 | `(receive_at - _emit_at.iso) × 1000` | locustfile L52 `(time.time() - emit_ts) * 1000`, emit_timing L34-35 `time.time() - emit_ts` | ✅ (locustfile ms, 단위 테스트 초) |

**A01-9 4 환경 매트릭스 — dict 포맷에서도 유지** (재검증).

| 환경 | `_emit_at` (dict) 응답에 살아남는지 | 가드 |
|---|---|---|
| 운영 | ❌ 부재 (페이로드 자체 미부착) | `maybe_add_emit_at` L11-12 noop ✅ |
| 테스트 + 평범 | ❌ strip | `expose_emit_at=False` → L44-46 미할당 ✅ |
| 테스트 + 임의 헤더 (`prod`) | ❌ strip | `is_test_client=False` → 동일 ✅ |
| 테스트 + `test` | ✅ 노출 (dict 그대로) | `expose_emit_at=True` → L46 `result[k] = v` ✅, M1 신규 테스트 L98-106 `result["_emit_at"] == emit_at_dict` 동등 검증 ✅ |

PR #1 의 5층 가드를 dict 포맷 변경 후에도 그대로 유지. 가드 약화 없음 ✅.

**M1 후속 (PR #1 정민 발견 보정).**

- `tests/unit/test_emit_timing.py:91-108 test_expose_emit_at_included_when_flag_true` — `expose_emit_at=True` + `is_test_client=True` 경로 단위 테스트 신설. emit_timing.py L45-46 (이전 L38-39) 미커버 해소. coverage `emit_timing.py 87% → 93%` (Missing 39-40, except 분기만 남음).
- M1 등급 격하 → 해소 ✅.

**locustfile 변경 (E1 픽스).**

- L44-56: `_emit_at` dict 파싱 분기 — `isinstance(emit_at, dict)` 가드 + `iso.get("iso")` 추출 + `replace("Z","+00:00")` defensive + `fromisoformat().timestamp()` → unix epoch → 차이 ms 계산. PR #1 의 float 기대 코드 → dict 파싱으로 정합.

**발견 사항.**

#### LOW (3건 — 모두 운영 영향 없음, 후속 1줄 커밋 권장)

- **L1. `load_tests/locustfile_sse_latency.py` — ruff F401 (unused-import) + I001 (unsorted-imports)**. L48 의 인라인 `from datetime import datetime, timezone` 위치 + 미사용 import. `ruff --fix` 1회 해결. **본 PR 차단 사유 아님 (load_tests/ 는 운영 코드 외)**, 후속 권장.
- **L2. `load_tests/locustfile_sse_latency.py:65-66` — ruff S110 try-except-pass**. 부하 측정 컨텍스트에서 한 샘플 실패가 전체 부하 발생을 막으면 안 됨 → silent 합리적. 단 silent-failure 정책상 명시적 카운터 또는 logger.debug 권장. LOW.
- **L3. `load_tests/locustfile_sse_latency.py:15` — ruff S311 (`random.choice`)**. 비암호학적 random 사용. 부하 테스트 사용자 선택용이라 보안 영향 0. 메모.

#### INFO (2건 — 향후 정합 보강 여지)

- **I1. ADR §5.4.3 iso 예시는 `Z` suffix 인데 코드는 `+00:00` 출력**. `datetime.now(UTC).isoformat()` 동작 — Python 표준. 양쪽 호환 (locustfile defensive), 운영 영향 없음. ADR 예시 보정 (Z → +00:00) 또는 코드 통일 (`isoformat() + "Z"` 형태로 `+00:00` 제거 후 `Z` 부착) 중 향후 결정. 본 PR 차단 사유 아님.
- **I2. emit_timing.py:34 strip 측에서 `monotonic_ns` 미사용**. ADR §5.4.3 의 "동일 머신 단조 시계 차이 검증용" — 시범 단일 인스턴스 환경에서 향후 정합 보강 (지터 검증·NTP drift 보호) 가능. 본 PR 차단 사유 아님.

#### 정합성 — 통과 확인 (강점)

- `maybe_add_emit_at` dict 출력 (L13-14) — ADR §5.4.3 SSOT 정확 구현 ✅
- `strip_internal_keys` L29-40 — `isinstance(emit_at, dict)` 가드 + `try/except (ValueError, TypeError, AttributeError)` 로 비-dict 입력 보호 ✅ (silent-failure 가 ADR §9 정책상 문제이나 측정 무시가 합리적이라 본 케이스 OK)
- `test_expose_emit_at_included_when_flag_true` — M1 정확 1줄 이상의 동등 검증 (`result["_emit_at"] == emit_at_dict`) + latency 기록 동시 ✅
- locustfile `replace("Z","+00:00")` defensive — ADR 명세와 코드 출력 양쪽 호환 ✅
- PR #1 의 5층 가드 (워커 부착·헤더 정확·strip·로그 금지·AND) dict 포맷 변경에도 모두 유지 ✅

#### 후속 (카맥 측 조치)

1. 본 PR 머지 → `locustfile_sse_latency.py` 재실행 → P-02 (SSE p95 < 500ms) + P-03 (push-to-receive) PromQL 시계열 정상 확인.
2. L1·L2·L3 후속 1줄 커밋 권장 (load_tests/ 영역, 게이트 차단 사유 아님).
3. I1·I2 향후 ADR 보강 여지 메모. 본 PR 무관.

#### 마크 4그룹 영향 (CTO 통지)

CTO 메시지 2026-05-19 15:01 — "E1 은 본 PR #2 에서 해결되므로 마크 4그룹 E 에서 E1 제거 가능". 마크 PR #3 재제출 시 E1 검증은 본 PR #2 머지 후 자동 충족 (emit_timing.py 가 본 PR 에서 갱신됨). 마크는 자신의 변경 영역에서 dict 포맷 가정만 유지하면 됨. E2 (네이선 발견) 정의는 여전히 정민 셋업 체크리스트 보존.


---

### PR #4 상세

**결론.** **머지 허용 (PR #4 범위)** — CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 0. CTO 결재 (a) hotfix 채택 (2026-05-19 15:19) 4건 확장 모두 해결. ADR §5.5 envelope 정합 회복 + ADR §4.1 BIGSERIAL 정합 회복 + H8 test code 필드 assert 추가.

**검증 시점 head SHA.** `3b84acf1ff540ab2b4e630ada5b0e13968927634` (origin/develop/taskq/hotfix-h3-envelope HEAD, 2026-05-19 15:34). ⑤ 단계 — 머지 직전 SHA 가 본 값과 일치하면 통과 유효. 신규 push 시 통과 무효 + 재검증 요구.

**ADR §8.1 5단계 자가 적용.**

| 단계 | 점검 | 결과 |
|---|---|---|
| ① `interface-change` 라벨 | envelope 본문 변경, code 카탈로그는 ADR §5.5 기 정의 | N/A (호환 변경 — 본문 형식 회복) |
| ② §4·§5·§6 경로 휴리스틱 | `middleware/session.py` (§6 인증), `blueprints/events.py` (§5 SSE), `models/job.py` (§4 데이터 모델), `services/job.py` (§4·§5 라이프사이클) | ✅ 4 경로 매칭 — 호환 변경으로 진행 |
| ③ 컨텍스트 라인 검증 | ADR §5.5 카탈로그 ↔ envelope 코드 (`UNAUTHENTICATED`/`NOT_FOUND`) 일치 | ✅ |
| ④ SSOT 트레이스 | [inspection-PR3-gate.md](inspection-PR3-gate.md) 4그룹 + [PR #3 사후 게이트 상세](#pr-3-사후-게이트-상세) HIGH 잔존 ↔ 본 PR 4건 확장 | ✅ |
| ⑤ 머지 직전 head SHA 명시 | 통과 코멘트 본문에 `3b84acf1ff540ab2b4e630ada5b0e13968927634` 명시 | ✅ |

**자동 게이트.**
- 단위/통합 ✅ 60 passed (마크 보고 일치)
- 커버리지 ✅ 81.34% (마크 보고 일치)
- 정적분석 ✅ ruff 0 (src + tests) / pyright 0 (src 전 영역)
- 의존성 ✅ pip-audit clean (마크 자가 보고 — 정민 재실행 시 환경 의존)

**해결 확인 (CTO 결재 4건 확장).**

| ID | 위치 | 검증 |
|---|---|---|
| H3-a | `middleware/session.py:26-27` | ✅ `body = {"error": {"code": "UNAUTHENTICATED", "message": "authentication required"}}` + `jsonify(body), 401` — ADR §5.5 정합 |
| H3-b | `blueprints/events.py:114` | ✅ `return jsonify({"error": {"code": "NOT_FOUND", "message": "job not found"}}), 404` — jsonify 호출 추가 + envelope 정합 |
| MEDIUM-신규 (event_id BIGSERIAL) | `models/job.py:68-70` + `services/job.py:51` | ✅ `BigInteger().with_variant(Integer, "sqlite")` — PG BIGSERIAL + SQLite Integer ROWID alias 양환경 autoincrement / `services/job.py:51` 의 `JobEvent(...)` 가 id 직접 지정 안 함 (자동 시퀀스 위임). 마크 옵션 (i) 채택 |
| H8 | `tests/integration/test_job_endpoints.py:231` | ✅ `assert resp.get_json()["error"]["code"] == "INVALID_TRANSITION"  # H8: code 필드 위치` — 실제로 해결됨. 마크 커밋 메시지 "3건" 은 정확하지 않음 (실제 4건). 본 게이트는 코드/테스트 기준이라 메시지 부정확은 LOW 메모 |

**정민 진단 보정 (자가 발견 — 정밀 grep 사후 보완)**

PR #3 사후 게이트 시 정민이 `grep -nE '"error"\s*:' src/{middleware,blueprints}/**/*.py` 자가 규칙을 명시했음에도 보고 본문에 `jobs.py + middleware/session.py + events.py` 만 언급. 본 PR #4 게이트 시 전수 grep 재수행으로 **`blueprints/auth.py` 의 envelope 잔존 3건 신규 발견**.

| ID | 위치 | 코드 |
|---|---|---|
| **H3-c (신규)** | `blueprints/auth.py:22` | `return jsonify({"error": "email and password required"}), 422` — `VALIDATION_FAILED` code 누락 |
| **H3-d (신규)** | `blueprints/auth.py:26` | `return jsonify({"error": "Invalid credentials"}), 401` — `UNAUTHENTICATED` code 누락 |
| **H3-e (신규)** | `blueprints/auth.py:61` | `return jsonify({"error": "User not found"}), 404` — `NOT_FOUND` code 누락 |

영향 — 시나리오 1 step 3 (로그인 실패 envelope) + 사용자 열거 방어 (security-audit.md A07-2) 정합. 본 PR #4 범위 외이므로 차단 사유 아님. **별도 후속 hotfix 권고** (한 PR 으로 envelope 정합 일괄 회복) — CTO 결재 요청.

**진단 자가 규칙 강화 (3번째 보강)**

- PR #1 H5 보정 (라벨 vs 헤더) — ADR §7.2 cross-check 의무화
- PR #3 사후 게이트 (envelope 누락) — `src/{middleware,blueprints}/**/*.py` 전체 grep 의무
- 본 PR #4 — **위 grep 을 실제로 전수 실행하고 결과를 본문에 인용**. 부분 인용으로 누락 표면 발생.

```bash
# 정민 자가 게이트 직전 체크 — 본 명령 결과 0건 또는 모든 매치가 envelope 정합 시 통과:
grep -nE '"error"[[:space:]]*:' src/middleware/*.py src/blueprints/*.py src/services/*.py
```

**후속 (마크 측)**

1. **PR #4 자체** — 머지 허용. ⑤ head SHA `3b84acf1ff540ab2b4e630ada5b0e13968927634` 와 머지 시점 SHA 일치 확인 후 머지.
2. **별도 후속 hotfix** (H3-c/H3-d/H3-e auth.py 3건) — 슬러그 `develop/taskq/hotfix-auth-envelope` 권고. `_err` 헬퍼 (jobs.py:26-28) 를 auth.py 에 동일 적용 + 시나리오 1 step 3 의 `error.code == "VALIDATION_FAILED"` 검증 동시 추가.
3. 커밋 메시지 정합 — 향후 PR 시 변경 건수 메시지와 실제 변경 일치. 본 PR 의 "3건" 은 H8 도 포함된 사실상 4건이었음.

**머지 시점 SHA 일치 ✅ (§8.1 5단계 적용)** — 머지 전 head SHA `3b84acf1ff540ab2b4e630ada5b0e13968927634` 와 정민 통과 코멘트 SHA 일치 확인 후 merge commit `5466e214c81f342f061062dcc80a7364ab239337` 생성 (2026-05-19).

#### CTO 알림 — 정민 진단 누락 자가 보정 (3번째)

PR #3 사후 게이트 시 H3 평가에서 auth.py 3건 누락. CTO 통지 + 별도 hotfix PR 채택 여부 결재 요청.

---

### PR #5 상세

**결론 (재검증 후 갱신, 2026-05-19 15:48).** **재검증 실패 — HIGH 2 회귀**. ⑤ 단계 룰이 즉시 작동하여 force-push 후 회귀를 검출. 1차 검증 (head `94436387`) 통과는 무효 처리. 마크 rebase 후 재게이트 필요.

#### 1차 검증 (무효)

- 검증 시점 head SHA: `94436387747f24573eed0589ed04576cf90a6c16` — 2026-05-19 15:44
- 결과: C0/H0/M0/L0 머지 허용 (envelope 전수 grep 6 라우트 정합 ✅)
- 무효 사유: 마크가 PostToolUse 훅 되돌림으로 flat 오류를 발견하고 강제 push → head 변경

#### 2차 검증 (재검증)

- 검증 시점 head SHA: **`9b4a2631a3c833eaadeb02f88b5255381195445f`** — 2026-05-19 15:48
- 자동 게이트: ✅ 60 passed / 81.39% cov / ruff 0 (자동 게이트 통과). **그러나 envelope 단위 테스트 부재로 회귀 미검출 — 자동 게이트 한계**
- **회귀 발견 (HIGH 2)**:

| ID | 위치 | 9b4a2631 의 상태 |
|---|---|---|
| **H3-a 회귀** | `middleware/session.py:26` | `return jsonify({"error": "Unauthorized"}), 401` — **PR #4 (3b84acf) 의 envelope 회복이 회귀, flat 으로 환원** |
| **H3-b 회귀** | `blueprints/events.py:114` | `return {"error": "Not found"}, 404` — **PR #4 의 envelope 회복 + jsonify 추가가 회귀, flat 환원 (jsonify 도 사라짐)** |
| H3-c | `auth.py:22` | ✅ VALIDATION_FAILED envelope (정상) |
| H3-d | `auth.py:27` | ✅ UNAUTHENTICATED envelope (정상) |
| H3-e | `auth.py:63` | ✅ NOT_FOUND envelope (정상) |

#### 원인 — base 분기 위치 오류

```bash
$ git merge-base --is-ancestor 3b84acf 9b4a2631
# EXIT=1  (3b84acf 가 9b4a2631 의 조상이 아님)

$ git log --oneline 9b4a2631 -3
9b4a263 fix(auth): ADR §5.5 오류 봉투 실제 적용 확인
d7b59d1 perf(locustfile): ...
7fef3db fix(jobs): PR #3 gate fixes
```

`9b4a2631` 의 부모가 `d7b59d1` — PR #4 (`3b84acf`) 가 부모 체인에 없음. 마크의 force-push 가 **잘못된 base** (PR #4 머지 이전 시점) 에서 분기되어 PR #4 의 fix 가 사라진 채로 auth.py 만 위에 얹힌 결과.

`origin/develop/taskq/v0.1.0` 의 HEAD 는 여전히 `3b84acf` (PR #4 머지 상태). 그러나 PR #5 branch `hotfix-auth-envelope` 가 force-push 로 부모 체인을 잃음.

#### ⑤ 단계 룰 작동 증명 — **영구 등재 (CTO 추인 2026-05-19 15:53)**

> 본 사례는 ADR-001 §8.1 게이트키퍼 운영 규칙 5단계의 첫 회귀 감지 성공 사례로 거버넌스 자산에 영구 등재한다.

| 단계 | 사건 | 결과 |
|---|---|---|
| **PR #4 머지** | head SHA `3b84acf`, envelope 정합 회복 (H3-a session.py + H3-b events.py) | v0.1.0 HEAD = `3b84acf` |
| **PR #5 1차** | head SHA `94436387` (부모 체인: `94436387 → 3b84acf → d7b59d1 → ...`) | 정민 게이트 통과 — 6 라우트 envelope 정합 ✅ |
| **PostToolUse 훅 되돌림** | 마크가 1차 코드의 flat 오류 발견 (커밋 인쇄와 워킹 카피 불일치) | 재커밋 + force-push |
| **PR #5 2차 (force-push)** | head SHA `9b4a2631` (부모 체인: `9b4a2631 → d7b59d1 → ...`, **`3b84acf` 부재**) | 정민 ⑤ 단계 재검증 수행 |
| **회귀 검출** | `git merge-base --is-ancestor 3b84acf 9b4a2631` → EXIT=1 + envelope grep 6 라우트 중 session.py·events.py flat 환원 | **HIGH 2 회귀** → 1차 통과 무효 + 재게이트 요구 |

**거버넌스 영구 자산**
- **룰 정합성 증명** — 머지 직전 head SHA 일치 검증이 force-push 후 부모 체인 변경을 탐지 가능함이 실증됨
- **자동 게이트 한계 노출** — ruff/pytest/coverage 모두 통과한 코드에 envelope 회귀가 존재. 단위 테스트 부재가 자동 게이트의 사각지대
- **§8.1 ① 단계 강화 후보 (Patch 5)** — 1차 트리거에서도 `git merge-base --is-ancestor <prev-PR-head> <current-PR-head>` 사전 검증을 의무화하면 force-push 사고를 ⑤ 단계까지 안 가도 ① 에서 차단 가능. 네이선 자율 시점 ADR §8.1 ① 절에 한 줄 추가 또는 정민 cross-ref docs PR 에 묶음 가능 (CTO 옵션 명시 2026-05-19 15:53)

#### 후속 (마크 측 조치 — CTO 결재 결과)

| 옵션 | 설명 | 정민 권고 | CTO 결재 |
|---|---|---|---|
| (a) rebase | `git rebase origin/develop/taskq/v0.1.0 hotfix-auth-envelope` 후 force-push | 권장 — 변경 자체는 작아 conflict 가능성 낮음 | **❌ 거절 (15:53)** — "force-push 패턴 자체가 사고 원인이라 격리 우선" |
| (b) v2 슬러그 재분기 | `develop/taskq/hotfix-auth-envelope-v2` 새 브랜치를 v0.1.0 최신 HEAD 에서 분기 후 5건 (복구 2 + 원래 3) 적용 | 슬러그 변경 시 CTO 거버넌스 룰 (슬러그 PR 별 고유) 충족 | **✅ 채택 (15:53)** — 마크에 별도 위임 송신 완료 |
| (c) PR #5 닫고 새 PR | 새 PR 발행 | 비권장 — PR 트레이스 분산 | 기각 |

**v2 PR 범위 (CTO 명시).**
- 복구 (PR #5 force-push 로 회귀된 2건): H3-a `middleware/session.py:26` envelope, H3-b `blueprints/events.py:114` envelope + jsonify
- 원래 (auth.py 3건): H3-c L22 VALIDATION_FAILED, H3-d L26 UNAUTHENTICATED, H3-e L61 NOT_FOUND
- base: `develop/taskq/v0.1.0` 최신 HEAD (CTO 인용 `5466e21` — PR #4 머지된 시점)

#### v2 PR 도착 시 게이트 가동 체크리스트 (CTO 운영 권한 추인 2026-05-19 15:57)

```bash
# ① 트리거 — 부모 체인 ancestor 검증 (강화)
git merge-base --is-ancestor 3b84acf <v2-head>   # EXIT=0 필수 (PR #4 fix 보존 확인)

# ② 경로 휴리스틱
grep -lE '"error"' src/middleware/*.py src/blueprints/*.py   # session·events·auth 3 영역

# ③ 컨텍스트 라인 — envelope 6 라우트 전수 grep
grep -nE '"error"[[:space:]]*:' src/middleware/*.py src/blueprints/*.py src/services/*.py

# ④ SSOT 트레이스 — PR #4 fix 보존 + auth 3건 추가
git diff origin/develop/taskq/v0.1.0 <v2-head> -- src/ tests/

# ⑤ 머지 직전 head SHA 명시 + envelope 단위 테스트 포함 여부
# - 통과 코멘트 본문에 <v2-head> 40-char SHA 명시
# - tests/integration/test_envelope_consistency.py (또는 동등) 포함 검증
```

**envelope 단위 테스트 권고 (CTO 통지 15:57).** PR #5 회귀가 자동 게이트 (ruff/pytest/coverage) 를 통과한 코드에서 발생한 한계 노출. CTO 가 마크에 v2 PR 에 envelope 단위 테스트 포함 권고했음을 본 게이트 검증 항목으로 명시 — **각 라우트의 4xx 응답이 `{"error":{"code":<str>, "message":<str>}}` 형식 지키는지 검증하는 단위 테스트 1건 이상 포함되면 통과 가산, 부재 시 MEDIUM 메모** (단, v2 PR 의 머지 차단 사유는 아님 — 별도 후속 PR 가능).

#### envelope 단위 테스트 부재 — 자동 게이트 한계 노출

본 회귀는 ruff/pytest 모두 통과한 상태에서 발생. envelope 정합을 검증하는 단위 테스트가 없어서 자동 게이트가 잡지 못함. **`audit-envelope-grep` docs PR 의 정신은 grep 게이트지만, 추가로 `tests/integration/test_envelope_consistency.py` (각 라우트의 4xx 응답 envelope 형식 검증) 도 필요**. PR #5 rebase 후 마크에 envelope 단위 테스트 추가 권고 (또는 정민 자율 PR).

#### 진단 자가 보정 누적 — 4번째

자동 게이트가 통과한 코드에 회귀가 있을 수 있다는 사실을 1차 검증에서 발견하지 못한 점. ⑤ 단계 룰이 다행히 잡아냈지만, 정민이 1차 검증 시 `git merge-base --is-ancestor PR-4-head PR-5-head` 검증을 했어야 함 (PR #5 가 PR #4 위에 빌드됐는지 확인). **진단 자가 규칙 4번째 — 다중 hotfix 시퀀스에서 head SHA 부모 체인에 직전 PR HEAD 포함 여부 검증 의무**.

**ADR §8.1 5단계 자가 적용.**

| 단계 | 점검 | 결과 |
|---|---|---|
| ① `interface-change` 라벨 | envelope 본문 형식 회복 — code 카탈로그 (ADR §5.5) 기 정의 | N/A (호환 변경) |
| ② §4·§5·§6 경로 휴리스틱 | `blueprints/auth.py` (§6 인증) | ✅ 단일 경로 |
| ③ 컨텍스트 라인 검증 | A07-2 사용자 열거 방어 (auth.py L25-28 User None + password 실패 → 단일 UNAUTHENTICATED) ADR §6.5 정합 | ✅ |
| ④ SSOT 트레이스 | [PR #4 상세](#pr-4-상세) §정민 진단 보정 ↔ 본 PR 3건 ↔ ADR §5.5 | ✅ |
| ⑤ 머지 직전 head SHA 명시 | 통과 코멘트 본문에 `94436387747f24573eed0589ed04576cf90a6c16` 명시 | ✅ |

**자동 게이트.**
- 단위/통합 ✅ 60 passed (마크 보고 일치)
- 커버리지 ✅ 81.39% (마크 보고 81.39% 일치)
- 정적분석 ✅ ruff 0 (src + tests). pyright 는 본 PR 시점 venv 설정 이슈로 정민 환경 미실행, 신규 오류 0건은 마크 자가 보고
- 의존성 ✅ pip-audit clean (마크 자가 보고)

**해결 확인.**

| ID | 위치 | 검증 |
|---|---|---|
| H3-c | `blueprints/auth.py:22-23` | ✅ `body = {"error": {"code": "VALIDATION_FAILED", "message": "email and password required"}}` + `jsonify(body), 422` — ADR §5.5 정합 |
| H3-d | `blueprints/auth.py:27-28` | ✅ `body = {"error": {"code": "UNAUTHENTICATED", "message": "invalid credentials"}}` + `jsonify(body), 401` — A07-2 사용자 열거 방어 단일 메시지 유지 (User None + password 실패 양 경로 동일 응답) |
| H3-e | `blueprints/auth.py:63` | ✅ `return jsonify({"error": {"code": "NOT_FOUND", "message": "user not found"}}), 404` |

**envelope 전수 grep 검증 — 6 라우트 모두 정합.**

```
middleware/session.py:26  UNAUTHENTICATED  ✅
blueprints/auth.py:22     VALIDATION_FAILED ✅
blueprints/auth.py:27     UNAUTHENTICATED  ✅
blueprints/auth.py:63     NOT_FOUND        ✅
blueprints/events.py:114  NOT_FOUND        ✅
blueprints/jobs.py:28     _err 헬퍼 (envelope 생성기) ✅
```

ADR §5.5 envelope 카탈로그 (`UNAUTHENTICATED`/`FORBIDDEN`/`CSRF_FAILED`/`VALIDATION_FAILED`/`RATE_LIMITED`/`IDEMPOTENCY_CONFLICT`/`INVALID_TRANSITION`/`NOT_FOUND`/`INTERNAL`) 와 현 코드의 응답 코드가 정확 일치. 정민의 자가 보정 → CTO 결재 → 마크 hotfix → 정민 재검증 사이클이 envelope 도메인 회복으로 완결됨.

**정합성 — 통과 확인 (강점)**

- A07-2 사용자 열거 방어 정합 ✅ — User None 과 password 실패 양 경로가 단일 응답으로 합쳐짐 (auth.py L25-28). 응답 시간 분산 검증은 별도 부하 테스트 영역
- `db.session.get(User, g.current_user_id)` (auth.py L61) — SQLAlchemy 2.0 권장 패턴 ✅ (PR #3 게이트 시 발견된 M10 `Query.get()` deprecation 패턴이 본 영역에서는 이미 정합)
- ⑤ head SHA 명시 — PR #1·#2 사고 (head 흡수 우회) 재발 방지 핵심 룰 준수

**후속 (자동 강화 권한 발동)**

- 반복 이슈 트래커 envelope 누락 항목 — 본 PR 머지 후 line-through 처리 + `audit-envelope-grep` docs PR (security-audit.md A05 envelope 전수 grep 게이트 한 줄 추가) 발행 트리거.
- 슬러그 `develop/taskq/audit-envelope-grep`. base `develop/taskq/v0.1.0`. 정민 자가 머지 (네이선 §8.1 ⑤ 단계 통과 코멘트 후).

---

### PR #6 상세

**결론.** **머지 허용 + 머지 완료** (2026-05-19 17:34). C0/H0/M0/L1. 3축 강화 게이트 모두 통과. CTO 결재 (b) PR 본문 명시 후 머지 (16:04) 결재 — 마크가 PR 본문에 docs commit (9a8484b) 명시 후 머지 진행.

**검증 시점 head SHA.** `9a8484b7b172d9f566b2c006c0805c0deade5f33`. v0.1.0 새 HEAD = `2932dad` (Merge hotfix-auth-envelope-v2). ⑤ 단계 — 머지 직전 origin head 와 통과 코멘트 SHA 일치 확인 ✅ (마크 보고 17:34).

**3축 강화 게이트.**

| 축 | 명령·결과 |
|---|---|
| ① 부모 체인 ancestor | `git merge-base --is-ancestor 3b84acf 9a8484b` → EXIT=0 (PR #4 fix `3b84acf` 보존 ✅, force-push 회귀 차단) |
| ② envelope 전수 grep 6 라우트 | session.py:26 UNAUTHENTICATED / auth.py L22 VALIDATION_FAILED / L27 UNAUTHENTICATED / L63 NOT_FOUND / events.py:114 NOT_FOUND / jobs.py:28 `_err` 헬퍼 ✅ |
| ③ envelope 단위 테스트 5건 | `test_auth_endpoints.py` 신규 — wrong_password / unknown_email / missing_fields / logout_without_session / me_without_auth (`error.code` assertion 5건) ✅ |

**자동 게이트.** 60 passed / 81.39% cov / ruff 0 / pip-audit clean / pyright pre-existing venv 이슈만.

**커밋 구조.**

```
2932dad Merge hotfix-auth-envelope-v2 (v0.1.0 새 HEAD)
9a8484b docs: review-log PR #3-#5 이력 + ADR-001 §8.1 5단계 룰 등재
582a0be fix(auth): H3-c/d/e envelope 적용 + envelope 단위 테스트 추가
3b84acf fix(api): 사후 게이트 H3-a/H3-b/MEDIUM 3건 수정 (PR #4)
```

- `582a0be` — 마크 코드·테스트 (auth.py +8 / test +10)
- `9a8484b` — docs commit (review-log +413 / ADR +31) — **정민 워킹 트리 변경분 의도 외 흡수**

#### docs 흡수 사고 — (b) PR 본문 명시 후 머지 (CTO 결재 16:04)

**사건.** PR #6 head `9a8484b` 가 정민 워킹 트리 변경분 (review-log §PR #2/§PR #3 사후/§PR #4/§PR #5/§6.A/§7 거버넌스 갱신 + ADR §8.1 보존본) 을 의도 외 흡수. 마크 PR 본문 보고는 코드 + 테스트만 명시.

**원인.** 모든 멤버 인스턴스가 같은 `jin.yu@vuno.co` git config 로 commit → 한 인스턴스 워킹 트리 변경분이 다른 인스턴스 commit 에 포함 가능 (§6 jin.yu 공통 git config 격리 룰 / §6.B 사고 트리오 3번째).

**결재.** CTO (b) 채택 — 마크에 PR 본문에 docs commit (9a8484b) 명시 요구. PR 본문 수정은 코드 SHA 변경 없음 → §8.1 5단계 통과 SHA `9a8484b7` 유효 유지. (a) revert 거절·(c) docs commit 분리 비권장 — 결과적으로 거버넌스 트레이스가 같은 PR 통합되어 효율적.

**LOW 1.** PR 본문 vs 실제 범위 불일치. CTO 결재 (b) 로 본문 사후 보강·머지. 머지 차단 사유 아님. PR #4 H8 "3건" 메시지 패턴과 동일.

**거버넌스 학습 자산.**
- 사고 트리오 3번째 — `§6.B` 영구 등재 (슬러그 충돌 / 페인 매핑 / git config 공통)
- §6 운영 메모 — "jin.yu 공통 git config 격리 룰" 한 줄

**Patch 5 후보 첫 운영 사례.** ① 단계 `git merge-base --is-ancestor 3b84acf 9a8484b` ancestor 검증을 본 PR #6 게이트에서 사실상 첫 운영. 네이선이 ADR 본문 등재 시점에 본 트레이스 인용 가능 (CTO 추인 15:53).

**정민 docs PR 트랙 무효화.** `docs/taskq/adr-patch4-and-reviewlog-cross-ref` 브랜치가 PR #6 의 9a8484b 흡수로 별도 발행 불필요. 본 PR (`governance-rollup-v0.1.0`) 에서 누락 등재 일괄 보강.

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
| 응답 envelope 누락 (ADR §5.5 `{error:{code,message}}` 미준수) | **4 (도메인 회복 미완)** | #3 / 사후 게이트 (H3-a·H3-b) / PR #4 게이트 신규 (H3-c·H3-d·H3-e auth.py) / **PR #5 재검증 회귀** (H3-a·H3-b session.py·events.py flat 환원, force-push base 분기 오류) | 자동 강화 권한 발동 ✅ — `audit-envelope-grep` docs PR + `tests/integration/test_envelope_consistency.py` 단위 테스트 추가 발행. 회귀 가능성 자체를 단위 테스트가 잡아야 한다는 사실이 PR #5 재검증으로 드러남 |
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
- [x] 마크 회신 6건 수신 — Q-A1 (SESSION_ABS_TTL_OVERRIDE_SEC 수용) / Q-A2 (CELERY_BACKOFF_BASE_SEC=0.1 수용) / Q-A4 (compose.multi.yml 별도 PR) / Q-S1 (로그 stdout 일원화) / Q-S2 (`.audit-ignore` 정민 승인 PR 방식) / Q-S3 (모든 PR a11y, spec 도착 시 활성) — 2026-05-19 15:14 완료. scenarios.md / security-audit.md / regression.md 본문 일괄 갱신은 후속 1건 PR
- [x] 마크 PR #3 fix 사후 게이트 — 13건 중 10건 해결, HIGH 3 잔존 (H3-a session, H3-b events, H8 test). hotfix 권고 송신. **CTO 결재 (a) hotfix PR 채택 — 2026-05-19 15:19**. 사고 후 사후 정합 부분 운영 인정. E1·E2 모두 해결됨 (E1 = 카맥 PR #2 dict 포맷 / E2 = 마크 fix `sse_messages_sent_total` 라벨 `[channel, event]`)
- [x] hotfix PR (마크) #4 머지 허용 — 2026-05-19 15:34 통과, head SHA `3b84acf1ff540ab2b4e630ada5b0e13968927634`. 슬러그 `develop/taskq/hotfix-h3-envelope`. 4건 확장 모두 해결 (H3-a/H3-b/MEDIUM(2)/H8). **단 정민 진단 누락 신규 발견** — auth.py H3-c/H3-d/H3-e 3건 envelope 잔존 → 별도 hotfix 권고. 원본 4건:
  - H3-a `middleware/session.py:26` — envelope `{error:{code:"UNAUTHENTICATED", message:...}}`
  - H3-b `blueprints/events.py:114` — envelope `{error:{code:"NOT_FOUND", message:...}}`
  - H8 `tests/integration/test_job_endpoints.py:209-231` — `INVALID_TRANSITION` code 필드 assert 추가
  - **MEDIUM (CTO 확장 4번째)** `services/job.py:52 event_id = uuid.uuid4().int >> 65` — ADR §4.1 `BIGSERIAL PRIMARY KEY` 정합 회복. 마크 옵션: (i) `event_id` 직접 채우지 않고 PG 시퀀스 의존, (ii) `event_ulid` 와 혼동 정정. CTO 결단 (2026-05-19 15:19) 으로 hotfix 범위에 편입 → 옵션 (i) 채택 ✅
- [ ] **후속 hotfix v2 — 마크 위임 진행 중**. CTO 결재 (b) v2 슬러그 채택 (2026-05-19 15:53). 슬러그 `develop/taskq/hotfix-auth-envelope-v2`. base `develop/taskq/v0.1.0` 최신 HEAD (CTO 인용 `5466e21`). 범위 5건 — **복구 2건** (H3-a session.py / H3-b events.py — PR #5 force-push 회귀 복구) + **원래 3건** (H3-c/H3-d/H3-e auth.py). v2 head SHA 보고 시 ⑤ 단계 재게이트. (a) rebase 거절 사유 — "force-push 패턴 자체가 사고 원인이라 격리 우선".
- [ ] **자동 강화 PR — `audit-envelope-grep` docs PR** (CTO 위임 권한 발동, 2026-05-19 15:38). security-audit.md A05 절에 envelope 전수 grep 게이트 한 줄 추가. 슬러그 `develop/taskq/audit-envelope-grep`. base `develop/taskq/v0.1.0`. PR #5 머지 + 현 adr-patch4 docs PR 머지 후 발행.
- [ ] CI 파이프라인 게이트 등록 (마크 협업) — 대기

---

## 6. 운영 메모

- 본 로그는 머지 후에도 절대 행 삭제하지 않음. 잘못된 행은 line-through (`~~...~~`) 처리 후 사유를 비고에 적는다.
- CRITICAL 발견 시 정민은 즉시 `team-send 제임스 "[CRITICAL] PR #__ ..."` 보고. 마크에게 차단 코멘트는 동시에 송신.
- MEDIUM/LOW 후속은 Jira Sub-task 생성 후 비고 컬럼에 키 기록.
- 분기 검토 — 반복 이슈 트래커가 3회 이상인 유형은 분기 회고에 안건으로 올린다.
- **발신자 식별 규약** (2026-05-19 15:21 CTO 정정 + 15:23 CTO 추인). tmux 페인 매핑이 일시 어긋날 수 있으므로 `team-send` 의 `[From: X → Y]` 헤더만 신뢰하지 않는다. **본문 첫 줄의 라벨 — `[CTO 제임스 ...]`, `[From: 마크 → 정민]`, `[결과] ...` 등 — 이 1차 SSOT**. 헤더와 본문 라벨이 다르면 본문 라벨 기준으로 응답. 본 규약은 페인 매핑 정정 전까지 유효. CTO 추인 메모 — "정민이 그동안 게이트 운영 회신에서 이미 본문 라벨 기준으로 발신자 식별 — 사고 발생 이전부터 자율 적용된 우수 패턴".
- **jin.yu 공통 git config 격리 룰** (2026-05-19 16:04 CTO 추인, PR #6 docs 흡수 사고 학습). 모든 멤버 인스턴스가 같은 `jin.yu@vuno.co` git user 로 커밋하므로 한 인스턴스의 워킹 트리 변경분이 다른 인스턴스의 commit 에 의도 외 흡수될 수 있다. **docs 작업은 git worktree 격리 또는 명시적 stash 격리 + 명시적 별도 브랜치 checkout 후 즉시 commit 후 진행**. 정민의 `adr-patch4-and-reviewlog-cross-ref` 트랙이 PR #6 의 9a8484b commit 으로 흡수되어 자동 무효화된 사건이 본 룰의 트리거.

### 6.A 진단 자가 보정 누적

> CTO 추인 2026-05-19 15:36 — "게이트 운영자가 자기 진단의 부정확을 정직 기록하는 패턴이 거버넌스 신뢰 핵심". 정민이 자기 발견·정정한 진단 부정확 사례를 누적 카운트한다. 향후 진단 자가 규칙 강화 트리거.

| # | 일자 | 사례 | 정정 위치 |
|---|---|---|---|
| 1 | 2026-05-19 15:11 | **H5 진단 부정확** — 라벨 부재가 결정적 원인인데 "헤더 검증 미구현" 부수 원인만 짚음 | [§PR #3 §HIGH H5](#pr-3-상세) 본문 끝 보정 한 줄 |
| 2 | 2026-05-19 15:34 | **PR #3 사후 게이트 envelope 영역 부분 grep** — `src/{middleware,blueprints}/**/*.py` 자가 규칙 명시했음에도 본문에 jobs+session+events 만 보고. PR #4 게이트 시 전수 grep 으로 auth.py 3건 정정 발견 | [§PR #4 상세](#pr-4-상세) §정민 진단 보정 |
| 3 | 2026-05-19 15:34 | **PR #4 마크 커밋 메시지 "3건" 검증** — 실제 H8 도 해결됨 (test L231). 메시지·코드 불일치를 게이트 결과에 정직 기록 | [§PR #4 상세](#pr-4-상세) H8 행 |
| 4 | 2026-05-19 15:48 | **PR #5 1차 검증 시 부모 체인 미검증** — 다중 hotfix 시퀀스 (PR #4 → PR #5) 에서 `git merge-base --is-ancestor` 로 직전 PR HEAD 가 현재 PR 부모 체인에 포함되는지 확인했어야 함. 1차 검증 시점에는 정합했으나 force-push 가능성을 사전 차단 못 함. ⑤ 단계 룰이 사후 검출 | [§PR #5 상세](#pr-5-상세) §원인·진단 자가 보정 누적 — 4번째 |
| 5 | 2026-05-19 17:34 | **PR #6 게이트 시 워킹 트리 격리 사전 수행 누락** — 정민의 워킹 트리에 적재된 docs 변경분이 마크 PR #6 의 9a8484b commit 으로 의도 외 흡수. 정민이 PR #6 게이트 가동 직전 git worktree 또는 stash 격리를 사전 수행하지 않은 점. CTO 통지 (b) 본문 명시 후 머지로 사후 보정. | [§PR #6 상세](#pr-6-상세) §docs 흡수 사고 + §6.B 사고 트리오 |

**진단 자가 규칙 누적 (보정에서 파생한 운영 규칙)**

- ADR §7.2 메트릭 카탈로그 cross-check 의무 (H5 보정 → PR #1 적용)
- `src/{middleware,blueprints}/**/*.py` envelope 전수 grep 의무 + 결과 본문 인용 (PR #3 → PR #4 적용)
- 커밋 메시지 의 변경 건수와 실제 코드/테스트 변경 일치 검증 (PR #4 보정)
- **다중 hotfix 시퀀스에서 부모 체인 검증 의무** — `git merge-base --is-ancestor <prev-PR-head> <current-PR-head>` 가 EXIT=0 인지 ① 단계와 ⑤ 단계 모두에서 확인 (PR #5 회귀 보정)
- **인터페이스 정합 회귀 차단을 위한 단위 테스트 의무** — envelope·event 카탈로그·메트릭 라벨처럼 자동 게이트 (ruff/pytest/coverage 합산) 가 잡지 못하는 도메인은 라우트·필드 일관성을 직접 검증하는 단위 테스트가 필수. PR #5 회귀 사례에서 ruff/pytest 통과한 코드에 envelope 회귀가 있었음 (CTO 통지 2026-05-19 15:57)
- **공통 git config 환경의 워킹 트리 격리 의무** — `jin.yu@vuno.co` 공통 config 환경에서 docs/거버넌스 작업은 git worktree 또는 명시적 stash 격리 + 즉시 commit 후 진행. PR #6 의 9a8484b 가 정민 워킹 트리 변경분 흡수한 사건 학습 (CTO 추인 2026-05-19 16:04)

### 6.B 거버넌스 학습 사고 트리오 (운영 환경 진입 시 룰 강화 권고)

> CTO 통지 2026-05-19 16:04 — 시범 프로젝트의 산출. 동일 패턴이 다른 팀·다른 프로젝트에 이식될 때 사전 차단 권고. 운영 환경 진입 시 ADR 또는 별도 `governance.md` 로 격상 (CTO 통지 2026-05-19 17:34).

| # | 사고 | 패턴 | 트리거 PR | 차후 룰 |
|---|---|---|---|---|
| 1 | 슬러그 충돌 (동시 작업) | `develop/taskq/pr3-gate-fixes` 가 카맥 PR #2 와 마크 PR #3 작업에서 동시 사용 → v0.1.0 머지 시 정민 미검증 fix(7fef3db) 흡수 | PR #2 ↔ PR #3 | §0 박스 — 슬러그 PR 별 고유 룰 (CTO 추인 15:09) |
| 2 | 페인 매핑 표류 | tmux 페인 매핑 헤더가 실제 발신자와 어긋남 (CTO 인스턴스가 페인 5 에 위치) | 페인 매핑 사고 (15:21) | §6 발신자 식별 규약 — 본문 첫 줄 라벨 1차 SSOT |
| 3 | jin.yu 공통 git config 흡수 | 워킹 트리 변경분이 다른 인스턴스 commit 에 흡수 | PR #6 docs commit 9a8484b 가 정민 docs 트랙 흡수 | §6 jin.yu 공통 git config 격리 룰 (본 절) |

세 사고 모두 **공통 인스턴스 운영 환경의 격리 부재** 가 근본 원인. 운영 환경 진입 시 (1) 멤버별 git user 분리, (2) 페인 매핑 자동 검증, (3) 슬러그 정책 자동 검사 CI 권고.

## 7. 거버넌스 SSOT 누적

> 시범 프로젝트 운영 중 합의된 거버넌스 규약의 1차 SSOT 위치를 표로 누적한다. 새 항목 추가 시 출처 (추인 일시·주체) 명시. CTO 통지 2026-05-19 15:23.

| # | 규약 | 1차 SSOT 위치 | 추인 |
|---|---|---|---|
| 1 | §8 게이트키퍼 5단계 (interface-change 라벨 / 경로 휴리스틱 / 컨텍스트 라인 / SSOT 트레이스 / 머지 직전 head SHA) | [ADR-001 §8.1](../decisions/ADR-001-architecture.md) — 네이선 영구 등재 (Patch 4) | CTO 2026-05-19 15:11 |
| 2 | 슬러그 PR 별 고유·동시 작업 금지 (재사용은 머지 완료 후) | 본 review-log §0 박스 | CTO 2026-05-19 15:09 (PR #2 우회 통합 사고 재발 방지) |
| 3 | 페인 헤더 vs 본문 라벨 SSOT — 본문 첫 줄 라벨이 1차 | 본 review-log §6 (정민 자율 등재) | CTO 2026-05-19 15:21 정정 + 15:23 추인 |
| 4 | _(예정)_ PR 본문 `author-role: <role>` 라벨 강제 | _(미등재)_ — 후속 review-log 갱신 시점에 §0 또는 별도 절 | 네이선 권고, 정민 자율 시점 발효 |
| 5 | _(Patch 5 후보)_ §8.1 ① 단계 강화 — 다중 hotfix 시퀀스에서 `git merge-base --is-ancestor <prev-PR-head> <current-PR-head>` 사전 검증 의무 | _(미등재)_ — 1차 SSOT 는 ADR-001 §8.1 ① 절 한 줄 추가 (네이선 영역). 2차는 본 review-log §6.A 진단 자가 규칙 누적 4번째 (이미 등재). **본 PR #6 게이트에서 첫 운영 사례** | CTO 추인 2026-05-19 15:53 — 네이선 자율 시점 ADR 본문 추가 또는 정민 cross-ref docs PR 묶음 |
| 6 | 거버넌스 학습 사고 트리오 (슬러그 충돌 / 페인 매핑 / git config 공통) — 공통 인스턴스 운영 환경의 격리 부재 근본 원인 + 운영 환경 진입 시 (1) 멤버별 git user 분리, (2) 페인 매핑 자동 검증, (3) 슬러그 정책 자동 검사 CI 권고 | 본 review-log §6.B (1차 SSOT). 운영 환경 진입 시 ADR 또는 별도 `governance.md` 격상 권고 | CTO 통지 2026-05-19 16:04 + 17:34 |
