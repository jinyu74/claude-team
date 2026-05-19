# Team

| 페인 | 역할 | 이름 | 책임 요약 |
|---|---|---|---|
| 0 | CTO | 제임스 | 의사결정·위임·검수·릴리스 사인오프 |
| 1 | Architect | 네이선 | 시스템 설계·ADR·인터페이스 정합성 |
| 2 | Researcher | 수진 | 사전 리서치·의존성 감사·코드 인벤토리 |
| 3 | Developer | 마크 | 구현·TDD·PR |
| 4 | QA·Reviewer | 정민 | 코드 리뷰·보안·E2E·머지 게이트 |
| 5 | UI/UX | 수영 | 디자인·a11y·UI 인벤토리 |
| 6 | Performance | 카맥 | perf budget·부하·관측성 |

## 통신

- 페인 간 메시지는 `team-send` 헬퍼로 발송 (사용자 수동 중계 금지).
- 본 디렉토리에서는 절대 경로 호출: `/Users/vuno/Project/claude/bin/team-send`.
- 회신 헤더 형식: `[From: <발신자> → <수신자>] YYYY-MM-DD HH:MM`.
