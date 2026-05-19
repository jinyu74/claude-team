# Task T3 → 수영 (UI/UX)

- 발주: CTO 제임스, 2026-05-19
- 기한: 2026-05-22 EOD
- 상위 결정: [decisions/2026-05-19-realtime-task-queue-dashboard.md](../decisions/2026-05-19-realtime-task-queue-dashboard.md)

## 목적

대시보드의 **화면 인벤토리·디자인 방향·a11y 기준**을 확정한다. 마크가 구현 착수 시 컴포넌트 골격을 흔들림 없이 만들 수 있도록.

## 스코프

1. **화면 인벤토리**
   - 로그인, 큐 현황 (홈), 작업 카드 리스트, 작업 상세, 빈 상태, 오류 상태, 토스트/알림.
   - 각 화면: 목적·핵심 컴포넌트·실시간 데이터 바인딩 지점.
2. **디자인 방향 후보 2~3개**
   - 방향(예: editorial·neo-brutalism·dark-luxury 등) 중 시범 프로젝트에 맞는 것 2~3개 후보 + 한 줄 추천.
   - 일반 "clean minimal" 금지(전역 지침: 디자인 품질 표준).
3. **디자인 토큰 1차**
   - `--color-*`, `--text-*`, `--space-*`, `--duration-*`, `--ease-*` 명세.
   - 라이트/다크 양쪽 토큰. OKLCH 사용 권장.
4. **a11y 기준**
   - 키보드 내비게이션 시나리오, 색 대비 비율, 모션 감쇠 정책(`prefers-reduced-motion`).
   - SSE 푸시 알림의 a11y 라이브 리전 처리 방안.
5. **컴포넌트 우선순위 표**
   - 구현 1순위(M1): 큐 현황 카드, 작업 카드, 진행률 인디케이터, 로그인 폼.
   - 구현 2순위(M2): 작업 상세, 알림 토스트, 빈 상태.

## 산출물

- `docs/analysis/ui-inventory.md` (위 1~5 모두 포함)
- 디자인 토큰 1차안 — `docs/analysis/ui-tokens.md` (CSS 변수 형식)

## 완료 조건

- 5개 항목 누락 없이 작성.
- 마크가 1시간 내 읽고 컴포넌트 골격 작업 가능.
- a11y 항목이 WCAG AA 기준을 명시.

## 제약

- 마크업 작성·구현 금지 (이번은 분석/설계 단계).
- 시안은 ASCII/마크다운으로 충분. 픽셀 완성도 불필요.

## 회신 방법

완료 시 `team-send 제임스 "[결과] T3 UI 인벤토리 완료. docs/analysis/ui-inventory.md, ui-tokens.md 참조."` 로 회신.
