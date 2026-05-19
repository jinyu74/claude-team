# Inspection: T5 — 정민 E2E·보안·회귀·게이트 운영

- 검수일: 2026-05-19 13:58
- 검수자: CTO 제임스
- 발신자: 정민 (QA · Reviewer)
- 회신: `[결과] T5 4종 완료. 마크 회신 필요 11건 명세 내 표기.`
- 산출물:
  - `docs/qa/scenarios.md` (286 lines) — 시나리오 8건
  - `docs/qa/security-audit.md` (259 lines) — OWASP A01~A10 + 디자인 게이트
  - `docs/qa/regression.md` (162 lines) — 27건 매트릭스
  - `docs/qa/review-log.md` (153 lines) — PR 게이트 운영

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | 위임 A·B·C·D·E 5개 100% + 자동화 인덱스·영역별 게이트 표 강화 |
| (b) 형식 준수 | ✅ | Given/When/Then·표·코드블록·P0/P1/P2 분류 일관 |
| (c) 누락 없음 | ✅ | 시나리오 8건 모두 G/W/T·실패 분류·자동화 위치, OWASP 10건, 회귀 27건 |
| (d) 품질 기준 충족 | ✅ | **`expectNoLeak()` 헬퍼**, jitter ±25% 허용, 단방향 위반 CRITICAL, R-006 보안 설정 강제, pickle/marshal 부재 강제, 마크 회신 11건 자율 정리 |
| (e) 후속 단계 정합 | ✅ | ADR-001 §3.4/§4.3/§6.3/§2.4/§5.4.1·수영 ui-tokens.md·수진 dependency-audit.md R-006·네이선 §8 모두 인용 |

**판정: 통과 (PASS)** — 수준 최고.

## 강점

- **시나리오 7 백필 단조성** — Last-Event-ID 재연결 후 첫 이벤트의 ULID 가 직전 lastEventId 보다 커야 함. ADR §2.4 의 운영급 보장을 직접 검증.
- **시나리오 8 Redis MONITOR** — sampler 락 효력을 1초 윈도우 publish 흔적으로 직접 측정. CTOOL 차원 검증.
- **A08-6 pickle/marshal 부재 (CRITICAL)** — Celery JSON 강제 (`task_serializer='json'`, `accept_content=['json']`). 운영 deserialization 공격 표면 0.
- **A09.a 로그 grep 6쌍 (CRITICAL)** — `password=`, `Bearer `, `sid=01J`, `csrf:01J`, `argon2id$`, `Traceback`/`/Users/`/`/home/`. 운영 응답·로그 노출 자동 검출.
- **시나리오 4 레이스 핸들링** — succeeded 와 canceled 경합 시 둘 다 허용하되 `succeeded → canceled` 역전이 발견되면 CRITICAL.
- **review-log.md 영역별 게이트 적용 표** — 변경 영역 → 보안/회귀/E2E 필수 절 매핑. 정민 PR 리뷰 시 결정 비용 0.
- **마크 회신 11건 자율 정리** — CTO 검수 부담을 합리적으로 분담. 자동화 직전 합의 형성 의도.

## CTO 답변 (즉시 4건)

| Q | 답변 |
|---|---|
| **Q-A3** (retry 시 Idempotency-Key 누락) | **누락 허용**. ADR §3.3 명시 ("누락 시 서버가 ULID 생성하여 응답에 포함"). E2E 는 양 경로(헤더 있음/없음) 모두 1회씩 |
| **Q-R1** (succeeded retry 허용 정책) | **(b) `failed`/`canceled` 만 허용**. 의미적 정합 우선. `succeeded` 의 재실행은 "복제(clone)" 별도 액션으로 후속 ADR 분리 (현 M1 범위 외). **네이선이 ADR-001 Patch 3 으로 §3.3 또는 §4.3 에 한 줄 명시 요청** |
| **Q-R2** (멀티 sid 쿠키 정책) | **Flask 기본(첫 번째 sid) 따름**. 명시 거부는 정상 클라이언트 영향 위험. 보안상 충돌 시 검증 실패로 자연스럽게 401. review-log 영역별 표에 "쿠키 파싱은 Flask 기본" 한 줄 추가 |
| **Q-R3** (LOAD 도구 k6 vs locust) | **locust 통일**. 카맥 T6 가 locust 기반(load-tests.md §3·§4). 도구 통일이 학습·운영 비용 절감 |

## 마크 회신 위임 (6건)

마크에게 다음 6건 회신 요청 송신 — 자동화 일정 영향이라 우선순위 높음.

- Q-A1 (SESSION_ABS_TTL_OVERRIDE_SEC 수용 여부)
- Q-A2 (CELERY_BACKOFF_BASE_SEC=0.1 수용 여부)
- Q-A4 (compose.multi.yml 첫 PR vs 별도 PR)
- Q-S1 (로그 출력 경로 — stdout 일원화 권장)
- Q-S2 (`.audit-ignore` 파일 PR 정책)
- Q-S3 (a11y 스캔 모든 PR 권장)

## 후속

- 정민: CTO 4건 답변 수용 후 시나리오·regression 명세에 반영. 마크 6건 회신 도착 시 자동화 코드 진입.
- 마크: 6건 회신 + 첫 PR. 첫 PR 도착 즉시 정민이 게이트 가동.
- 네이선: Q-R1 결정에 대한 ADR-001 Patch 3 — `succeeded` 는 retry 불가 (§3.3 또는 §4.3 한 줄). 호환 변경.
- 카맥: locust 통일 합의 — load-tests.md 와 정민 LOAD-1/2 의 도구 일치 확인.
