# Realtime Task Queue Dashboard — 시범 프로젝트 (taskq)

7명 팀(제임스·네이선·수진·마크·정민·수영·카맥) 의 협업 역량 검증을 위한 시범 프로젝트.

- **스택**: React + TypeScript + Vite (FE) / Python + Flask + Redis + PostgreSQL + Celery (BE)
- **도메인**: 실시간 작업 큐 대시보드 (인증·작업 제출·Celery 워커·SSE 푸시·관측성)
- **평가 4축**: 기능(E2E) · 코드 품질(≥80%) · 성능(perf budget) · 보안·아키텍처

## 시작 지점

| 문서 | 내용 |
|---|---|
| [docs/decisions/2026-05-19-realtime-task-queue-dashboard.md](docs/decisions/2026-05-19-realtime-task-queue-dashboard.md) | CTO 결정 메모 — 범위·옵션·평가 4축·후속 |
| [docs/decisions/ADR-001-architecture.md](docs/decisions/ADR-001-architecture.md) | 시스템 아키텍처 ADR (Patch 1+2+3 포함) |
| [docs/roadmap.md](docs/roadmap.md) | 단계별 로드맵 |
| [docs/team.md](docs/team.md) | 팀 구성·통신 규약 |
| [docs/risks.md](docs/risks.md) | 리스크 레지스터 |

## 브랜치 전략

- **`main`** — 안정 상태 (분석·설계 산출물 + 머지 완료된 코드)
- **`develop/taskq/v0.1.0`** — M1 통합 브랜치
- **`develop/taskq/<slug>`** — 태스크 단위 PR 브랜치 (예: `auth`, `jobs-api`, `sse`, `web-shell`)

`main` 머지 시 태그(`v0.1.0` 등) 부여. 인터페이스 변경 PR 은 `interface-change` 라벨 + 네이선(Architect) 승인 필수 (ADR-001 §8).

## 통신

- 페인 간 메시지는 `team-send` 헬퍼 사용 (`/Users/vuno/Project/claude/bin/team-send`).
- 본 프로젝트에서는 Jira 면제 — 위임 지시서(`docs/tasks/T*.md`) 와 검수 로그(`docs/qa/inspection-*.md`) 가 트레이스 SSOT.
