# 실시간 작업 큐 대시보드 — 디자인 토큰 1차안

- 작성: 수영 (UI/UX), 2026-05-19
- 발주: CTO 제임스 (T3)
- 디자인 방향: Dark Command Center (라이트 모드 지원)
- 연관 문서: [ui-inventory.md](./ui-inventory.md)

---

## 사용 지침

- 모든 색상은 **OKLCH** 함수형 표기. 브라우저 지원 확인 필요 시 postcss-oklch 플러그인 사용.
- 다크 모드를 **기본값**으로, `:root[data-theme="light"]` 또는 `@media (prefers-color-scheme: light)` 로 라이트 오버라이드.
- `--space-*` 는 4px 베이스 그리드.
- `--text-*` 는 `clamp()` 기반 유동 크기.
- `--duration-*` / `--ease-*` 는 `prefers-reduced-motion: reduce` 구간에서 duration 0ms 로 오버라이드.

---

## tokens.css 전체

```css
/* 실시간 작업 큐 대시보드 디자인 토큰 — 1차안 (수영, 2026-05-19) */

/* ─────────────────────────────────
   다크 모드 기본값 (Dark Command Center)
   ───────────────────────────────── */
:root {

  /* ── 색상: 서피스 ── */
  --color-surface:              oklch(12% 0.007 250);   /* 페이지/카드 배경 */
  --color-surface-elevated:     oklch(17% 0.009 250);   /* 팝업/모달/elevated 카드 */
  --color-surface-hover:        oklch(20% 0.009 250);   /* hover 상태 */
  --color-surface-active:       oklch(22% 0.010 250);   /* active/pressed 상태 */

  /* ── 색상: 텍스트 ── */
  --color-text:                 oklch(94% 0 0);         /* 본문 기본 텍스트 */
  --color-text-muted:           oklch(58% 0 0);         /* 보조 라벨, 타임스탬프 */
  --color-text-disabled:        oklch(38% 0 0);         /* 비활성 텍스트 */
  --color-text-inverse:         oklch(12% 0 0);         /* 밝은 배경 위 텍스트 */

  /* ── 색상: 강조 (액션, CTA) ── */
  --color-accent:               oklch(64% 0.20 250);    /* primary 버튼, 링크 */
  --color-accent-hover:         oklch(68% 0.20 250);
  --color-accent-active:        oklch(60% 0.20 250);
  --color-accent-subtle:        oklch(25% 0.08 250);    /* 액센트 tint 배경 */

  /* ── 색상: 상태 (작업 큐 핵심) ── */
  --color-status-pending:       oklch(72% 0.14 85);     /* 대기중 — 앰버 */
  --color-status-pending-bg:    oklch(22% 0.06 85);
  --color-status-running:       oklch(64% 0.20 250);    /* 진행중 — 블루 (액센트와 동일) */
  --color-status-running-bg:    oklch(22% 0.08 250);
  --color-status-done:          oklch(68% 0.18 150);    /* 완료 — 그린 */
  --color-status-done-bg:       oklch(20% 0.07 150);
  --color-status-failed:        oklch(62% 0.22 25);     /* 실패 — 레드 */
  --color-status-failed-bg:     oklch(20% 0.09 25);

  /* ── 색상: 피드백 (토스트, 배너) ── */
  --color-feedback-success:     oklch(68% 0.18 150);
  --color-feedback-success-bg:  oklch(20% 0.07 150);
  --color-feedback-error:       oklch(62% 0.22 25);
  --color-feedback-error-bg:    oklch(20% 0.09 25);
  --color-feedback-warning:     oklch(72% 0.14 85);
  --color-feedback-warning-bg:  oklch(22% 0.06 85);
  --color-feedback-info:        oklch(64% 0.20 250);
  --color-feedback-info-bg:     oklch(22% 0.08 250);

  /* ── 색상: 보더 / 분리선 ── */
  --color-border:               oklch(25% 0.010 250);   /* 카드·입력 테두리 */
  --color-border-strong:        oklch(35% 0.012 250);   /* 구분선, 강조 테두리 */
  --color-border-focus:         oklch(64% 0.20 250);    /* 포커스 링 */

  /* ── 색상: 포커스 ── */
  --color-focus-ring:           oklch(64% 0.20 250);

  /* ── 색상: 오버레이 ── */
  --color-overlay:              oklch(0% 0 0 / 60%);    /* 모달 백드롭 */
  --color-overlay-hover:        oklch(100% 0 0 / 5%);   /* 카드 hover tint */


  /* ─────────────────────────────────
     타이포그래피
     ───────────────────────────────── */

  /* 폰트 패밀리 */
  --font-sans:   "Inter", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  --font-mono:   "JetBrains Mono", "Fira Code", "Consolas", monospace;

  /* 크기 (유동 clamp) */
  --text-xs:     clamp(0.6875rem, 0.65rem + 0.2vw, 0.75rem);    /* 10~12px: 타임스탬프, 메타 */
  --text-sm:     clamp(0.8125rem, 0.75rem + 0.3vw, 0.875rem);   /* 13~14px: 라벨, 보조 */
  --text-base:   clamp(0.9375rem, 0.88rem + 0.35vw, 1rem);      /* 15~16px: 본문 */
  --text-md:     clamp(1rem, 0.95rem + 0.3vw, 1.125rem);        /* 16~18px: 서브헤딩 */
  --text-lg:     clamp(1.125rem, 1rem + 0.6vw, 1.375rem);       /* 18~22px: 섹션 헤딩 */
  --text-xl:     clamp(1.375rem, 1.1rem + 1.2vw, 1.875rem);     /* 22~30px: 페이지 타이틀 */
  --text-2xl:    clamp(1.875rem, 1.4rem + 2vw, 2.5rem);         /* 30~40px: 큐 카운트 숫자 */

  /* 줄 높이 */
  --leading-tight:  1.2;
  --leading-normal: 1.5;
  --leading-loose:  1.75;

  /* 자간 */
  --tracking-tight:  -0.02em;
  --tracking-normal:  0em;
  --tracking-wide:    0.04em;   /* 상태 배지 레이블, 버튼 */

  /* 굵기 */
  --font-normal:   400;
  --font-medium:   500;
  --font-semibold: 600;
  --font-bold:     700;


  /* ─────────────────────────────────
     스페이싱 (4px 베이스 그리드)
     ───────────────────────────────── */

  --space-0:  0;
  --space-1:  0.25rem;   /*  4px */
  --space-2:  0.5rem;    /*  8px */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */

  /* 시맨틱 스페이싱 */
  --space-card-padding:    var(--space-5);          /* 카드 내부 패딩 */
  --space-section-gap:     var(--space-8);           /* 섹션 간 간격 */
  --space-page-inset:      clamp(var(--space-4), 4vw, var(--space-12));  /* 페이지 좌우 여백 */


  /* ─────────────────────────────────
     레이아웃
     ───────────────────────────────── */

  --radius-sm:   4px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-full: 9999px;

  --shadow-sm:   0 1px 3px oklch(0% 0 0 / 30%);
  --shadow-md:   0 4px 16px oklch(0% 0 0 / 40%);
  --shadow-lg:   0 8px 32px oklch(0% 0 0 / 50%);

  --z-base:      1;
  --z-dropdown:  100;
  --z-banner:    200;
  --z-modal:     300;
  --z-toast:     400;


  /* ─────────────────────────────────
     모션
     ───────────────────────────────── */

  --duration-instant:  50ms;
  --duration-fast:     150ms;   /* 호버, 포커스 링 */
  --duration-normal:   250ms;   /* 토스트 진입, 모달 열기 */
  --duration-slow:     400ms;   /* 페이지 전환, 레이아웃 변경 */

  --ease-out-expo:     cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out:       cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring:       cubic-bezier(0.34, 1.56, 0.64, 1);   /* 토스트 진입 */
}


/* ─────────────────────────────────
   라이트 모드 오버라이드
   ───────────────────────────────── */
/* data-theme 속성으로 라이트 모드 강제 지정 시 */
:root[data-theme="light"] {
  /* 서피스 */
  --color-surface:              oklch(98% 0 0);
  --color-surface-elevated:     oklch(100% 0 0);
  --color-surface-hover:        oklch(95% 0 0);
  --color-surface-active:       oklch(92% 0 0);

  /* 텍스트 */
  --color-text:                 oklch(12% 0 0);
  --color-text-muted:           oklch(44% 0 0);
  --color-text-disabled:        oklch(62% 0 0);
  --color-text-inverse:         oklch(94% 0 0);

  /* 강조 */
  --color-accent:               oklch(52% 0.20 250);
  --color-accent-hover:         oklch(48% 0.20 250);
  --color-accent-active:        oklch(44% 0.20 250);
  --color-accent-subtle:        oklch(93% 0.05 250);

  /* 상태 */
  --color-status-pending:       oklch(52% 0.14 85);
  --color-status-pending-bg:    oklch(95% 0.04 85);
  --color-status-running:       oklch(52% 0.20 250);
  --color-status-running-bg:    oklch(93% 0.05 250);
  --color-status-done:          oklch(48% 0.18 150);
  --color-status-done-bg:       oklch(93% 0.05 150);
  --color-status-failed:        oklch(48% 0.22 25);
  --color-status-failed-bg:     oklch(96% 0.04 25);

  /* 피드백 */
  --color-feedback-success:     oklch(48% 0.18 150);
  --color-feedback-success-bg:  oklch(93% 0.05 150);
  --color-feedback-error:       oklch(48% 0.22 25);
  --color-feedback-error-bg:    oklch(96% 0.04 25);
  --color-feedback-warning:     oklch(52% 0.14 85);
  --color-feedback-warning-bg:  oklch(95% 0.04 85);
  --color-feedback-info:        oklch(52% 0.20 250);
  --color-feedback-info-bg:     oklch(93% 0.05 250);

  /* 보더 */
  --color-border:               oklch(88% 0 0);
  --color-border-strong:        oklch(74% 0 0);
  --color-border-focus:         oklch(52% 0.20 250);

  /* 포커스 */
  --color-focus-ring:           oklch(52% 0.20 250);

  /* 오버레이 */
  --color-overlay:              oklch(0% 0 0 / 40%);
  --color-overlay-hover:        oklch(0% 0 0 / 4%);

  /* 그림자 (라이트) */
  --shadow-sm:   0 1px 3px oklch(0% 0 0 / 10%);
  --shadow-md:   0 4px 16px oklch(0% 0 0 / 12%);
  --shadow-lg:   0 8px 32px oklch(0% 0 0 / 16%);
}

/* OS 시스템 설정이 라이트이고 다크 강제 지정이 없는 경우 */
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    /* 서피스 */
    --color-surface:              oklch(98% 0 0);
    --color-surface-elevated:     oklch(100% 0 0);
    --color-surface-hover:        oklch(95% 0 0);
    --color-surface-active:       oklch(92% 0 0);

    /* 텍스트 */
    --color-text:                 oklch(12% 0 0);
    --color-text-muted:           oklch(44% 0 0);
    --color-text-disabled:        oklch(62% 0 0);
    --color-text-inverse:         oklch(94% 0 0);

    /* 강조 */
    --color-accent:               oklch(52% 0.20 250);
    --color-accent-hover:         oklch(48% 0.20 250);
    --color-accent-active:        oklch(44% 0.20 250);
    --color-accent-subtle:        oklch(93% 0.05 250);

    /* 상태 */
    --color-status-pending:       oklch(52% 0.14 85);
    --color-status-pending-bg:    oklch(95% 0.04 85);
    --color-status-running:       oklch(52% 0.20 250);
    --color-status-running-bg:    oklch(93% 0.05 250);
    --color-status-done:          oklch(48% 0.18 150);
    --color-status-done-bg:       oklch(93% 0.05 150);
    --color-status-failed:        oklch(48% 0.22 25);
    --color-status-failed-bg:     oklch(96% 0.04 25);

    /* 피드백 */
    --color-feedback-success:     oklch(48% 0.18 150);
    --color-feedback-success-bg:  oklch(93% 0.05 150);
    --color-feedback-error:       oklch(48% 0.22 25);
    --color-feedback-error-bg:    oklch(96% 0.04 25);
    --color-feedback-warning:     oklch(52% 0.14 85);
    --color-feedback-warning-bg:  oklch(95% 0.04 85);
    --color-feedback-info:        oklch(52% 0.20 250);
    --color-feedback-info-bg:     oklch(93% 0.05 250);

    /* 보더 */
    --color-border:               oklch(88% 0 0);
    --color-border-strong:        oklch(74% 0 0);
    --color-border-focus:         oklch(52% 0.20 250);

    /* 포커스 */
    --color-focus-ring:           oklch(52% 0.20 250);

    /* 오버레이 */
    --color-overlay:              oklch(0% 0 0 / 40%);
    --color-overlay-hover:        oklch(0% 0 0 / 4%);

    /* 그림자 (라이트) */
    --shadow-sm:   0 1px 3px oklch(0% 0 0 / 10%);
    --shadow-md:   0 4px 16px oklch(0% 0 0 / 12%);
    --shadow-lg:   0 8px 32px oklch(0% 0 0 / 16%);
  }
}


/* ─────────────────────────────────
   모션 감쇠 (prefers-reduced-motion)
   ───────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-instant:  0ms;
    --duration-fast:     0ms;
    --duration-normal:   0ms;
    --duration-slow:     0ms;
  }
}
```

---

## 토큰 사용 가이드

### 색상 선택 기준

| 상황 | 사용 토큰 |
|---|---|
| 페이지 배경 | `--color-surface` |
| 카드·패널 배경 | `--color-surface-elevated` |
| 본문 텍스트 | `--color-text` |
| 날짜·ID·보조 정보 | `--color-text-muted` |
| 주요 액션 버튼 | `--color-accent` |
| 대기 상태 표시 | `--color-status-pending` + `--color-status-pending-bg` |
| 진행 상태 표시 | `--color-status-running` + `--color-status-running-bg` |
| 완료 상태 표시 | `--color-status-done` + `--color-status-done-bg` |
| 실패 상태 표시 | `--color-status-failed` + `--color-status-failed-bg` |
| 오류 토스트·배너 | `--color-feedback-error` + `--color-feedback-error-bg` |
| 구분선 | `--color-border` |
| 포커스 링 | `--color-focus-ring` |

### StatusBadge 패턴 (색 + 아이콘 + 텍스트 3종 필수)

```
대기중:  bg = --color-status-pending-bg  /  text = --color-status-pending  /  아이콘 ○
진행중:  bg = --color-status-running-bg  /  text = --color-status-running  /  아이콘 ●
완료:    bg = --color-status-done-bg     /  text = --color-status-done     /  아이콘 ✓
실패:    bg = --color-status-failed-bg   /  text = --color-status-failed   /  아이콘 ✕
```

### 대비 검증 체크포인트

다크 모드에서 최소 대비비 확인 필요 쌍.

| 전경 토큰 | 배경 토큰 | 최소 대비 |
|---|---|---|
| `--color-text` | `--color-surface` | 4.5:1 이상 |
| `--color-text-muted` | `--color-surface` | 4.5:1 이상 (소형 텍스트) |
| `--color-status-pending` | `--color-status-pending-bg` | 4.5:1 이상 |
| `--color-status-running` | `--color-status-running-bg` | 4.5:1 이상 |
| `--color-status-done` | `--color-status-done-bg` | 4.5:1 이상 |
| `--color-status-failed` | `--color-status-failed-bg` | 4.5:1 이상 |
| `--color-border` | `--color-surface` | 3:1 이상 (UI 컴포넌트) |
| `--color-focus-ring` | 주변 배경 | 3:1 이상 |

> 구현 단계에서 정민이 자동화 대비 검사 도구(axe-core, Playwright a11y 스캔)로 검증.

### 스페이싱 시맨틱 예시

```
카드 내부 패딩:     var(--space-card-padding)   → var(--space-5) = 20px
카드 간 간격:       var(--space-4)              → 16px
섹션 헤딩 여백:     var(--space-6)              → 24px
QueueStatusCard 행 gap: var(--space-4)          → 16px
페이지 좌우 인셋:   var(--space-page-inset)     → clamp(16px, 4vw, 48px)
```

### 모션 예시

```css
/* 버튼 hover */
.button {
  transition: background-color var(--duration-fast) var(--ease-out-expo);
}

/* 토스트 진입 */
.toast-enter {
  animation: toast-slide-in var(--duration-normal) var(--ease-spring) forwards;
}

/* ProgressBar 진행률 갱신 */
.progress-fill {
  transition: width var(--duration-slow) var(--ease-in-out);
}

/* prefers-reduced-motion 에서는 위 duration이 모두 0ms가 됨 */
```

---

## 변경 이력

| 날짜 | 변경 | 작성자 |
|---|---|---|
| 2026-05-19 | 1차 초안 작성 | 수영 |
| 2026-05-19 | 라이트 모드 selector+@media 콤마 연결 → 두 블록으로 분리 (CSS 문법 수정) | 수영 |
