# Inspection: ADR-001 Patch 2 + Patch 3 — 동일 PR 묶음

- 검수일: 2026-05-19 14:00
- 검수자: CTO 제임스
- 발신자: 네이선 (Architect)
- 회신: `[결과 사본] ADR-001 Patch 2+3 완료. (5층 다층 가드 + 자동/수동 retry 분리)`
- 산출물: `docs/decisions/ADR-001-architecture.md` (517 → 592 lines, +75)

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | 위임 초과 — Patch 2 는 §5.4 한 단락 요청 → §5.4.3 + §7.2 + §1.2 + OWASP A01·A09. Patch 3 은 한 줄 요청 → §3.2 분할 + §4.3 표 + §5.1 + 오류 코드 카탈로그 |
| (b) 형식 준수 | ✅ | ADR 형식·패치 노트·한국어 마침표 유지 |
| (c) 누락 없음 | ✅ | 5층 다층 가드·종결 상태 3개 액션 표 모두 |
| (d) 품질 기준 충족 | ✅ | 다층 가드 운영급, 타이밍 오라클 위협 분석, ISO + monotonic_ns 두 포맷 의도 분리, 자동/수동 retry 분리 |
| (e) 후속 단계 정합 | ✅ | 정민 SM-4·카맥 baseline §4.1·inspection-T6 모두 출처 명시. 마크 분기 코드 예시 포함 |

**판정: 통과 (PASS)** — 위임 지시서 수준을 초과.

## Patch 2 (`_emit_at`) 강점

| 가드 층 | 위반 시 결과 | 비고 |
|---|---|---|
| 워커 부착 가드 | 페이로드 자체에 필드 없음 | `ENABLE_EMIT_AT=true` 만 활성 |
| 운영 빌드 미설정 | 활성화 코드 경로 비활성 | 운영 환경 변수가 false/미설정 기본값 |
| API strip | `_` prefix 식별 → 응답 직렬화 시 제거 | 런타임 규약 — 단순 누락 방지 |
| 클라이언트 헤더 | `X-Perf-Client: test` 미존재 시 strip | 일반 브라우저는 항상 strip |
| 로그 출력 금지 | 구조화 로그 필드에 미포함 | 사이드채널 차단 |

- **노출 AND 조건** `ENABLE_EMIT_AT=true ∧ X-Perf-Client: test` — 운영 누출 확률 사실상 0.
- **ISO + monotonic_ns 두 포맷** — NTP 동기 환경 차이 계산 vs 동일 머신 단조 시계 검증 분리. 의도 명확.
- **타이밍 오라클 위협 분석** — 단순 "노출 금지" 가 아니라 IDOR/처리비용 추론 위협까지 명시.

## Patch 3 (수동 retry) 강점

- **§3.2 자동/수동 분리** — Celery `autoretry_for` 와 PATCH `action:retry` 의 의미 차이를 명시. 이전엔 모호했음.
- **§4.3 종결 상태별 액션 표** — `succeeded` / `failed` / `canceled` 각각의 허용·거부 액션을 한 표에 정리. 마크 구현·정민 회귀 양쪽 직접 참조.
- **`clone` 액션 분리** — `succeeded` 재실행 수요를 부정하지 않고 별도 ADR 로 분리 — 의사결정 추적 가능.
- **`INVALID_TRANSITION` 오류 코드** — 카탈로그에 추가. 정민 SM-4 에 즉시 인용 가능.

## 후속 (영향 인지 동기화)

| 담당 | 인지·반영 사항 |
|---|---|
| **마크** | T4 구현에 §5.4.3 코드 분기 그대로 인용. 워커 부착 분기 + API strip 미들웨어 + 로그 필드 제외 3 지점. `INVALID_TRANSITION` 오류 코드 카탈로그 등록 |
| **카맥** | `load_tests/locustfile_sse_latency.py` 의 요청에 `X-Perf-Client: test` 헤더 명시. `client_type=test` 라벨이 등재됐으므로 `check_budget.py` 의 P-02/P-03 라벨 필터 재확인 |
| **정민** | `scenarios.md` SM-4 상태 `❓ 마크 회신 후` → `✅ HIGH` 로 갱신 가능 (ADR 명시 완료). `security-audit.md` 에 `_emit_at` 운영 누출 시 CRITICAL 한 줄 추가 권고 |

## 패치 노트

- 본 검수 통과로 ADR-001 의 Patch 2+3 채택 확정.
- 이후 호환 변경은 패치 노트 누적, 비호환 변경만 ADR-002 발행 (§8 절차 유지).
