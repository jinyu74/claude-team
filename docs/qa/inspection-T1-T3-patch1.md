# Inspection: ADR-001 Patch 1 + UI Inventory v2 — 정합 보강

- 검수일: 2026-05-19 13:40
- 검수자: CTO 제임스
- 발신자: 네이선 (ADR Patch 1), 수영 (UI 인벤토리 v2)
- 산출물:
  - `docs/decisions/ADR-001-architecture.md` (457→517 lines, +60)
  - `docs/analysis/ui-inventory.md` (479→478 lines, 이름만 치환)

## 정합 최종 확인

| 영역 | ADR-001 §5.4 (네이선) | UI Inventory (수영) | 결과 |
|---|---|---|---|
| 제출 | `job.submitted` | `job.submitted` (EmptyState 해제, JobList 상단 삽입) | ✅ 일치 |
| 시작/성공/실패/취소 | 4종 분할 | `job.started/succeeded/failed/canceled` 4종 구독 | ✅ 일치 |
| 진행률 | `job.progress` (U 1s throttle / D raw) | `job.progress` (ProgressBar 바인딩) | ✅ 일치 |
| 큐 카운트 | `queue.counts` 1s throttle/debounce + 동일값 skip | `queue.counts` (QueueStatusCard, aria-live polite) | ✅ 일치 |
| 워커 | `queue.workers` 5s 주기 | `queue.workers` (WorkerStatusCard) | ✅ 일치 |
| 로그 | `log_line` D채널 max 200 bytes/line | `log_line` D채널 (LogViewer, aria-live off) | ✅ 일치 |
| 채널 분리 | U=`/api/events/jobs`, D=`/api/events/jobs/:id` | U/D 동일 명명 | ✅ 일치 |

**판정: 양쪽 통과 (PASS)**. 잔여 구식 이벤트명 0건.

## 네이선 Patch 1 의 추가 강점

- **§5.4.1 단일 리더 sampler** — `heartbeat:queue_emitter` Redis 키 `SET NX EX 10`. 멀티 API 인스턴스 환경에서 `queue.counts/workers` 중복 발행 방지. 위임 지시서에 없던 운영 디테일을 자율 추가.
- **§5.4 동일값 skip(debounce)** — `queue.counts` 가 직전 publish 와 같으면 SSE 송신 skip. 클라이언트 ACK·렌더 비용 절감.
- **§5.4 log_line 라인당 max 200 bytes** — 페이로드 폭주 보호.
- **§5.1 `/api/events/jobs/:id`** 에 **소유자 검증** 명시 — IDOR 차단.
- **§7.2 메트릭에 `channel` 라벨 + `queue_emitter_leader` gauge 신설** — 카맥 perf 게이트 직접 활용 가능.

## 보강 후 상태

- ADR-001 — Accepted (Patch 1, 2026-05-19)
- UI Inventory — v2 (이벤트명 ADR 표준 적용)
- 정합성 — 100% (이벤트·채널·빈도 정책 모두 일치)

## 2차 위임 트리거

보강 완료. 마크(구현)·정민(E2E/리뷰)·카맥(perf budget) 2차 위임 즉시 발주 가능.
