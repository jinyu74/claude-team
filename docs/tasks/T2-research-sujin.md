# Task T2 → 수진 (Researcher)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-22 EOD
- 상위 결정: [decisions/2026-05-19-realtime-task-queue-dashboard.md](../decisions/2026-05-19-realtime-task-queue-dashboard.md)

## 목적

ADR-001 작성 중인 네이선과 구현 착수 예정인 마크가 즉시 활용할 수 있도록 **실시간 큐 스택의 사전 리서치 노트**를 작성한다. 새로 짤 코드를 최소화하고, 검증된 패턴을 채택하는 것이 핵심.

## 스코프

1. **스켈레톤 / 참고 저장소 5개**
   - Flask + Celery + Redis + SSE/WebSocket 실시간 대시보드 패턴 가진 OSS 5건 식별.
   - 각각: 라이선스, 마지막 커밋, 별점, 우리 요구사항 충족률(%), 채택/포트 권장 여부.
   - GitHub 검색(`gh search repos/code`) 우선, Exa 는 보완용.
2. **핵심 라이브러리 비교 표**
   - SSE: Flask-SSE vs 직접 구현(`Response(stream_with_context)`)
   - WebSocket: Flask-Sock vs flask-socketio
   - Celery 모니터링: Flower vs 커스텀 SSE
   - PG ORM: SQLAlchemy 2.0 vs raw asyncpg-via-psycopg
   - 각 라이브러리: 유지보수 상태, 최근 1년 릴리스, 알려진 이슈, 우리 스택 호환 여부.
3. **CVE / 보안 감사**
   - 후보 라이브러리들의 OSV/GHSA 최근 1년 CVE.
   - HIGH/CRITICAL 발견 시 대안 제시.
4. **실시간 옵션 PoC 권장 시나리오**
   - 네이선의 SSE 잠정안 검증을 위한 간단한 PoC 절차(셸 명령 한 묶음).
   - 측정 항목: 연결 유지 시간, 푸시 지연, 1k 동시 연결 시 메모리.
5. **위험·블로커**
   - 리서치 중 발견한 미해결 질문 항목별 정리.

## 산출물

- `docs/analysis/research-realtime-stack.md`
- `docs/analysis/dependency-audit.md` 신설 (CVE 표 포함)

## 완료 조건

- 5개 OSS 평가표 채워짐.
- 라이브러리 비교 결론이 한 줄 권고(`채택` / `보류` / `거절`) 로 명시됨.
- CVE 표에서 모든 후보 라이브러리가 다뤄짐.

## 제약

- 채택 권고는 근거(별점·릴리스 빈도·CVE) 와 함께. 의견만 적는 것 금지.
- 리서치 결과는 ADR-001 의 의사결정 재료로 직접 사용 가능해야 함.

## 회신 방법

완료 시 `team-send 제임스 "[결과] T2 리서치 완료. docs/analysis/research-realtime-stack.md, dependency-audit.md 참조."` 로 회신.
