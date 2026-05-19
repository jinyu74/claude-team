# Inspection: T6 — 카맥 perf 베이스라인·budget·부하·대시보드

- 검수일: 2026-05-19 13:55
- 검수자: CTO 제임스
- 발신자: 카맥 (Performance)
- 회신: `[결과] T6 베이스라인·budget 초안 완료. (산출물 4종 + 협업 요청 2건)`
- 산출물:
  - `docs/performance/baseline.md` (163 lines)
  - `docs/performance/regression-perf.md` (123 lines)
  - `docs/performance/load-tests.md` (525 lines)
  - `infra/grafana/dashboard.json` (995 lines)

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | 위임 A~E 5개 항목 모두. 추가 budget 2건(`/healthz`, 에러율) 자체 강화 |
| (b) 형식 준수 | ✅ | 마크다운·표·코드(Python/Bash/YAML/JSON)·한국어 마침표 |
| (c) 누락 없음 | ✅ | N=10 + SD, warm/cold 분리, 48 매트릭스 + 우선 16, P-01~P-08 모두 자동화 상태 명시 |
| (d) 품질 기준 충족 | ✅ | `_emit_at` 운영 노출 금지·테스트 빌드 한정, `check_budget.py` 종료코드로 CI 통합 가능, `run_matrix.sh` 단일 명령 매트릭스, 베이스라인 TBD 솔직 표기 |
| (e) 후속 단계 정합 | ✅ | ADR-001 §7.2 메트릭 카탈로그 매핑 표·§5.4.1 sampler 락(P-06)·§5.4 throttle 정책 모두 연결 |

**판정: 통과 (PASS)**

## 강점

- **`_emit_at` 메커니즘** — UTC ISO-8601 + monotonic_ns 부착, 테스트 빌드 전용·운영 노출 금지·`sse_emit_to_receive_seconds` 라벨 격리. 보안 의식 우수.
- **P-06 리더 락 승계 측정 스크립트** — `docker kill` 후 `queue_emitter_leader` gauge 폴링하여 승계 시간 검증. ADR §5.4.1 운영 디테일을 자동화로 회수.
- **`check_budget.py` CI 헬퍼** — Prometheus 메트릭 직접 파싱, 임계값 비교, 종료코드 0/1 → GitHub Actions 단계로 그대로 흡수 가능.
- **`run_matrix.sh`** — 16종 매트릭스 단일 명령 + CSV·HTML·docker stats 자동 기록.
- **수진 PoC 흡수 표** — 누가 무엇을 흡수했는지 추적 가능. 산출물 재활용성 보장.
- **자체 추가 budget 2건** — `/healthz` p95 < 50ms (LB 헬스체크 신뢰성), API 에러율 < 0.1% (정상 부하 기준) — 평가 4축 성능 축 보강.

## 추가 budget 승인 근거

| 추가 항목 | budget | 승인 근거 |
|---|---|---|
| `/healthz` p95 | < 50ms | LB 헬스체크는 인프라 신뢰도. 50ms 는 합리적 상한 |
| API 에러율 (정상 부하) | < 0.1% | 503/502 제외(인프라 재시작) 명시 — SRE 표준 SLO 수준 |

## CTO 결정 사항

1. **regression-perf.md §1 Perf Budget 표 — 승인 (제임스 사인오프 2026-05-19)**.
   - 8개 항목 모두 채택. 향후 변경은 본 문서 §3.3 절차 (제임스 승인) 적용.
2. **per-PR CI 게이트 — P-01·P-02 가동 승인**.
   - 마크 첫 PR 부터 발효. 마크 T4 의 `.github/workflows/perf-gate.yml` 작성 시 §5 예시 사용.
3. **_emit_at 구현 협업 — 네이선·카맥·마크 3자 합의 후 진행**.
   - 카맥이 메커니즘 설계 완료. 네이선이 ADR §5.4 또는 §7.2 에 한 줄 등재 (호환 변경, ADR-001 Patch 2). 마크가 구현.

## 후속

- 카맥: PR 게이트 가동 (`load_tests/check_budget.py` + GitHub Actions 워크플로). 마크 첫 PR 도착 시 P-01·P-02 실행.
- 네이선: ADR-001 Patch 2 — `sse_emit_to_receive_seconds` 메트릭 + `_emit_at` 필드(테스트 빌드 전용) 등재.
- 마크: T4 BE 구현에 `_emit_at` 부착 분기(테스트 빌드 환경 변수 가드).
- 정민: 보안 audit 에 "`_emit_at` 운영 응답 누출 금지" 항목 추가.
