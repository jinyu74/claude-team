# Inspection: T1 — 네이선 ADR-001 시스템 아키텍처

- 검수일: 2026-05-19 13:35
- 검수자: CTO 제임스
- 발신자: 네이선 (Architect)
- 회신: `[결과] T1 ADR-001 완료. docs/decisions/ADR-001-architecture.md 참조. (요약 포함)`
- 산출물: `docs/decisions/ADR-001-architecture.md` (457 lines), `docs/decisions/index.md` 갱신

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | 위임 지시서 §1~§8 항목 모두 포함, OWASP 매핑까지 |
| (b) 형식 준수 | ✅ | ADR 표준 형식, TL;DR 표·SQL·JSON·다이어그램 |
| (c) 누락 없음 | ✅ | §1 컨텍스트, §2 실시간(옵션·근거·재연결·팬아웃·거절안), §3 큐(우선순위·재시도·idempotency·격리), §4 PG+Redis 스키마, §5 엔드포인트 10건+이벤트 7건+오류 카탈로그, §6 인증(argon2id·쿠키·CSRF·revoke), §7 로그·메트릭·트레이스, §8 변경 절차 |
| (d) 품질 기준 충족 | ✅ | API p95<200ms, SSE p95<500ms 구조적 근거 명시. argon2id·CSRF double-submit·IDOR 차단·HttpOnly+Secure+SameSite=Lax·acks_late+task_reject_on_worker_lost. Last-Event-ID + Redis Stream 백필 운영급. |
| (e) 후속 단계 정합 | ⚠️ → ✅ | UI 인벤토리(T3) 이벤트명과 불일치 1건. 통과 후 보강 위임으로 해결. ADR 자체 결함 아님 |

**판정: 통과 (PASS)** — 단, (e) 정합성 보강 2건 발주.

## 강점

- TL;DR 표 한 장에 의사결정자가 알아야 할 모든 핵심이 응축.
- §2.4 재연결 정책이 단순한 `Last-Event-ID` 가 아니라 Redis Stream MAXLEN + TTL 30분 + 100건/60초 백필이라는 운영급 디테일까지 명세.
- §3.3 idempotency 가 PG UNIQUE + 짧은 Redis 락 60s 이중 방어.
- §6.4 활동 슬라이딩 갱신 + revokeAllFor 가 비밀번호 변경 트리거에까지 연결.
- §7.3 trace_id 가 API → Celery payload 까지 전파.
- §8 변경 절차로 ADR 후 인터페이스 드리프트를 사전 차단.
- OWASP A01~A10 각 한 줄 매핑.

## 발견된 정합성 이슈 (보강 필요, blocker 아님)

**ADR §5.4 이벤트 카탈로그** vs **UI 인벤토리(T3) 의 SSE 바인딩** 간 명칭 불일치.

| UI 인벤토리(수영) | ADR §5.4 (네이선) | 처리 |
|---|---|---|
| `job.created` | `job.submitted` | UI 인벤토리 갱신 (ADR 표준 채택) |
| `job.done` | `job.succeeded` | UI 인벤토리 갱신 |
| `job.updated` (종합) | `job.started`/`job.succeeded`/`job.failed`/`job.canceled` 분할 | UI 인벤토리에서 종합 이벤트는 ADR 의 4종을 모두 구독해 카드 상태 갱신 |
| `progress` | `job.progress` | UI 인벤토리 갱신 |
| `queue.counts` (대기/진행/완료/실패) | **ADR 미정의** | ADR-001 §5.4 에 추가 발행 |
| `queue.workers` (워커 수·처리량) | **ADR 미정의** | ADR-001 §5.4 에 추가 발행 |
| `log_line` (작업 로그 스트리밍) | **ADR 미정의** | ADR-001 §5.4 에 추가 (스코프 합의 후) |

## 후속 보강 위임 (즉시 발주)

1. **네이선** — ADR-001 §5.4 에 다음 이벤트 추가.
   - `queue.counts {pending, running, succeeded, failed}` — 1초 throttle, 디바운스
   - `queue.workers {active, total, throughput}` — 5초 주기
   - `log_line {jobId, line, at}` — 작업 상세 화면 전용. 별도 SSE 채널 `/api/events/jobs/:id` 사용 권고 검토
2. **수영** — UI 인벤토리의 이벤트명을 ADR §5.4 명세에 맞춰 갱신 (수영의 종합 `job.updated` → 4종 구독으로 분기).

## 후속 (마크·정민·카맥 게이트)

- 마크: 본 ADR 의 §4 마이그레이션부터 착수 가능 (네이선 보강은 §5.4 만, §4 스키마는 영향 없음).
- 정민: §5 엔드포인트 10개 + 이벤트 7+3 종(보강 후) 에 대한 회귀 시나리오 8건 정의.
- 카맥: §7.2 메트릭 카탈로그 기반 perf 베이스라인. SSE 전송 지연 측정용 `sse_messages_sent_total` + 클라 수신 타임스탬프 회신 메커니즘 필요 — 카맥 검토.
