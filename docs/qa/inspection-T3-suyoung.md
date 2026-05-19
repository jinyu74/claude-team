# Inspection: T3 — 수영 UI 인벤토리·디자인 토큰

- 검수일: 2026-05-19 13:35
- 검수자: CTO 제임스
- 발신자: 수영 (UI/UX)
- 회신: `[결과] T3 UI 인벤토리 완료. docs/analysis/ui-inventory.md, ui-tokens.md 참조.`
- 산출물:
  - `docs/analysis/ui-inventory.md` (479 lines)
  - `docs/analysis/ui-tokens.md` (337 lines)

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | 화면 7개·디자인 후보 3+1·토큰·a11y 4축·우선순위 표 모두 포함 |
| (b) 형식 준수 | ✅ | 마크다운, 표·ASCII·CSS 변수 명세, 한국어 마침표 |
| (c) 누락 없음 | ✅ | 위임 지시서 5개 항목 전부 |
| (d) 품질 기준 충족 | ✅ | WCAG 2.2 AA·OKLCH·`prefers-reduced-motion`·aria-live polite/assertive 분리·"clean minimal" 금지 준수·포커스 링 외곽선 금지 명시 |
| (e) 후속 단계 정합 | ✅ | 파일 경로 예정·컴포넌트 의존·SSE 이벤트명(`queue.counts`, `job.updated`, `job.done`, `job.failed`, `log_line`)이 ADR-001 후보와 일관 |

**판정: 통과 (PASS)**

## 강점

- "Dark Command Center" 방향 추천이 도메인(운영 모니터링) 과 정합. 일반화된 "clean minimal" 함정 회피.
- aria-live 처리를 이벤트별로 정밀 분리 (큐 카운트 polite / job.failed assertive / log_line off).
- 상태 표시 3종 병기(색+아이콘+텍스트) — 색맹·저시력 사용자 고려.
- M0/M1/M2 우선순위 표가 마크 구현 일정과 직접 매핑 가능.
- 검수 가능한 대비표 — 정민이 axe-core/Playwright 로 자동 검증할 체크포인트 명시.

## 권고 (마이너, blocker 아님)

1. **`ui-tokens.md` 라이트 모드 CSS 문법** — selector 와 `@media` at-rule 을 콤마로 연결한 구조는 무효. 마크 구현 시 두 블록 분리 필요.
   ```css
   /* AS-IS (무효) */
   :root[data-theme="light"],
   @media (prefers-color-scheme: light) {
     :root:not([data-theme="dark"]) { ... }
   }

   /* TO-BE */
   :root[data-theme="light"] { /* ... */ }
   @media (prefers-color-scheme: light) {
     :root:not([data-theme="dark"]) { /* ... */ }
   }
   ```
2. **테마 토큰 변경 이력**은 ui-tokens.md 하단에 이미 있음 — 마크 PR 마다 갱신하도록 인계.

## 후속

- 수영: 통과 회신. M2 산출(작업 상세·필터바·로그뷰어) 시안은 마크 골격 완성 후 2차에 보강.
- 마크: 구현 단계에서 위 권고 1번 정리. M0/M1 컴포넌트 골격부터 착수.
- 정민: 대비표(7쌍) 자동 검증을 PR 게이트에 등재.
