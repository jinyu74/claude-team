# Task T1 → 네이선 (Architect)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-22 EOD
- 상위 결정: [decisions/2026-05-19-realtime-task-queue-dashboard.md](../decisions/2026-05-19-realtime-task-queue-dashboard.md)

## 목적

실시간 작업 큐 대시보드의 **시스템 아키텍처**를 ADR-001 로 확정한다. 마크가 ADR 확정 직후 바로 구현에 들어갈 수 있을 만큼 인터페이스·데이터 모델·실시간 채널 규약이 결정되어 있어야 한다.

## 스코프

ADR-001 한 건에 다음을 모두 담는다.

1. **시스템 컨텍스트 다이어그램** — FE(React/Vite), API(Flask), 워커(Celery), Redis, PostgreSQL 간 데이터 흐름.
2. **실시간 통신 결정** — SSE vs WebSocket vs 폴링. 잠정 결론은 SSE 1차. 검증·기각·근거 명시.
   - 양방향 명령(작업 취소 등) 의 처리 경로 명시.
   - 끊김·재연결·`Last-Event-ID` 정책.
   - 멀티 워커 환경에서의 이벤트 팬아웃(예: Redis pub/sub).
3. **큐 모델** — 우선순위 큐 사용 여부, 태그/큐 라우팅, 재시도·백오프 정책, idempotency key 사용처.
4. **데이터 모델** — `users`, `jobs`, `job_events` 최소 스키마. PK·인덱스·상태 머신(`pending → running → succeeded|failed|canceled`).
5. **API 인터페이스 1차** — 엔드포인트 표 (METHOD, PATH, REQ/RES 형태). SSE 채널 경로와 이벤트 페이로드 형식 포함.
6. **인증·세션** — 세션 + Redis 저장 채택. 쿠키·CSRF·로그아웃·만료 정책.
7. **관측성 훅** — 로그 필드, 메트릭(요청·큐 길이·작업 latency), 트레이스 ID 전파.
8. **인터페이스 변경 시 절차** — ADR-001 이후 인터페이스 수정은 PR 에 네이선 승인 필수.

## 산출물

- `docs/decisions/ADR-001-architecture.md` — 위 1~8 모두 포함.
- `docs/decisions/index.md` 에 ADR-001 상태 갱신.

## 완료 조건

- 위 항목 누락 없이 작성.
- 마크가 1시간 내 읽고 구현 착수 가능한 수준의 명확도.
- 정민·카맥이 게이트 기준을 도출 가능한 수준.

## 제약

- 시범 프로젝트. 분산·멀티리전·결제 도입 금지(과설계 방지).
- 실시간 푸시 지연 p95 < 500ms, API p95 < 200ms 를 ADR 단계에서 의식.
- 보안: OWASP Top 10 위협을 ADR 안에서 항목별로 1줄씩 언급.

## 회신 방법

완료 시 `team-send 제임스 "[결과] T1 ADR-001 완료. docs/decisions/ADR-001-architecture.md 참조."` 로 회신.
재질의는 동일 채널 사용.
