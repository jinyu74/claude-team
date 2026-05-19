# 실시간 작업 큐 대시보드 — UI 인벤토리 · 디자인 방향 · a11y 기준

- 작성: 수영 (UI/UX), 2026-05-19
- 발주: CTO 제임스 (T3)
- 기준 커밋: 초안 (코드베이스 미개발 단계)
- 연관 문서: [결정 문서](../decisions/2026-05-19-realtime-task-queue-dashboard.md), [디자인 토큰](./ui-tokens.md)

---

## 1. 화면 인벤토리

### 공통 조건

- 스택: React + TypeScript + Vite
- 실시간 통신: SSE (`/events/queue`, `/events/jobs/{id}`)
- 인증: 세션 기반, Redis 저장

---

### 화면 1 — 로그인 (Login)

**목적.** 이메일+비밀번호 인증, 세션 생성. 인증 실패 피드백.

**핵심 컴포넌트**

| 컴포넌트 | 역할 |
|---|---|
| `LoginForm` | 폼 컨테이너, submit 핸들링 |
| `EmailInput` | 이메일 입력, validation |
| `PasswordInput` | 비밀번호 입력 (toggle visibility) |
| `Button[primary]` | 로그인 제출 |
| `ErrorMessage` | 인증 오류 인라인 표시 |

**실시간 바인딩.** 없음 (단방향 submit → 리다이렉트).

**ASCII 스케치**

```
┌──────────────────────────────────┐
│                                  │
│         ■ 앱 로고/제목           │
│                                  │
│  ┌────────────────────────────┐  │
│  │ 이메일                      │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │ 비밀번호              [👁] │  │
│  └────────────────────────────┘  │
│                                  │
│  [오류: 이메일 또는 비밀번호 불일치] │  ← 조건부
│                                  │
│  [        로그인        ]        │
│                                  │
└──────────────────────────────────┘
```

---

### 화면 2 — 큐 현황 홈 (Queue Overview)

**목적.** 전체 큐 상태 요약, 워커 상태, 최근 작업 리스트를 한눈에 파악.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `AppHeader` | 앱명 + 사용자 메뉴 | — |
| `QueueStatusCard` × 4 | 대기/진행/완료/실패 카운트 | `/events/queue` → `queue.counts` |
| `WorkerStatusCard` | 활성 워커 수 + 처리량 | `/events/queue` → `queue.workers` |
| `JobList` (최신 20개) | 작업 카드 목록 | `/events/queue` → `job.started / job.succeeded / job.failed / job.canceled` |
| `SSEConnectionBanner` | SSE 연결 끊김 경고 | SSE 연결 상태 |

**실시간 바인딩 지점**

- `QueueStatusCard` — `queue.counts.{pending,running,done,failed}` 이벤트 수신 시 숫자 갱신
- `WorkerStatusCard` — `queue.workers` 이벤트 수신 시 워커 수/처리량 갱신
- `JobList` — `job.started / job.succeeded / job.failed / job.canceled` 이벤트 수신 시 해당 카드 상태 갱신 (전체 재요청 없음)

**ASCII 스케치**

```
┌─────────────────────────────────────────────────────┐
│ ■ Queue Dashboard                     [user@vuno ▾] │  ← AppHeader
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
│  │ 대기중    │  │ 진행중    │  │  완료    │  │ 실패   │  ← QueueStatusCard
│  │   127    │  │    8     │  │  3,421   │  │   12   │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘
│                                                     │
│  ┌──────────────────────────────────────────────────┐
│  │ 워커: 4/4 활성  ·  처리량: 2.3 job/s            │  ← WorkerStatusCard
│  └──────────────────────────────────────────────────┘
│                                                     │
│  ┌──────────────────────────────────────────────────┐
│  │ ID        상태     진행률      경과     액션      │  ← JobList 헤더
│  ├──────────────────────────────────────────────────┤
│  │ job-0042  진행중  ████░░ 67%  00:12   [취소]     │
│  │ job-0041  완료    ██████100%  00:28   [상세]     │
│  │ job-0040  실패    ██░░░░ 34%  00:05   [재시도]   │
│  │ ...                                              │
│  └──────────────────────────────────────────────────┘
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### 화면 3 — 작업 카드 리스트 (Job List)

**목적.** 전체 작업 목록 탐색, 상태·태그 필터, 재시도·취소 액션.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `FilterBar` | 상태/태그/날짜 필터, 검색 | — |
| `JobCard` | 단위 작업 행 (ID·상태·진행률·시간·액션) | `job.started / job.succeeded / job.failed / job.canceled` → 해당 카드 상태 갱신 |
| `StatusBadge` | 상태 칩 (pending/running/done/failed) | — |
| `ProgressIndicator` | 진행률 바 | `job.progress` |
| `Button[ghost]` — 취소 | PATCH `/jobs/{id}/cancel` | — |
| `Button[ghost]` — 재시도 | POST `/jobs/{id}/retry` | — |
| `PaginationBar` | 페이지네이션 | — |

**실시간 바인딩 지점**

- 개별 `JobCard` — `job.started / job.succeeded / job.failed / job.canceled` 이벤트의 `id` 매칭 후 `status`, `progress`, `elapsed` 갱신
- 신규 작업 진입 — `job.submitted` 이벤트 수신 시 리스트 상단 삽입 (애니메이션 선택적)

**ASCII 스케치**

```
┌──────────────────────────────────────────────────────────┐
│ [상태▾] [태그▾] [날짜▾]           [ 🔍 검색          ]  │  ← FilterBar
├──────────────────────────────────────────────────────────┤
│ ID         상태        진행률        경과    액션         │
├──────────────────────────────────────────────────────────┤
│ job-0042   ● 진행중   ████░░ 67%    0:12   [취소][상세]  │  ← JobCard
│ job-0041   ✓ 완료     ██████100%    0:28         [상세]  │
│ job-0040   ✕ 실패     ██░░░░ 34%    0:05   [재시도][상세]│
│ job-0039   ○ 대기중   ─────── 0%    0:00         [상세]  │
│ ...                                                      │
├──────────────────────────────────────────────────────────┤
│                    [ ← 1 2 3 … 48 → ]                   │  ← PaginationBar
└──────────────────────────────────────────────────────────┘
```

---

### 화면 4 — 작업 상세 (Job Detail)

**목적.** 단일 작업 상세 정보(메타데이터·로그·에러 트레이스), 재시도·취소 액션.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `JobDetailHeader` | ID·상태·최초 제출 시각 | `job.started / job.succeeded / job.failed / job.canceled` → status |
| `ProgressBar` (대형) | 진행률 상세 | `/events/jobs/{id}` → `job.progress` |
| `MetadataTable` | payload·우선순위·태그·워커 ID | — |
| `LogViewer` | 실시간 로그 스트리밍 | `/events/jobs/{id}` → `log_line` 스트리밍 |
| `ErrorTrace` | 실패 시 스택 트레이스 | — (정적, 실패 후 로드) |
| `Button[primary]` — 재시도 | POST `/jobs/{id}/retry` | — |
| `Button[destructive]` — 취소 | PATCH `/jobs/{id}/cancel` | — |

**실시간 바인딩 지점**

- `ProgressBar` — `/events/jobs/{id}` 전용 SSE 스트림 → `job.progress` 실시간 갱신
- `LogViewer` — 같은 스트림 → `log_line` 이벤트 수신 시 로그 라인 append
- `JobDetailHeader` `StatusBadge` — `job.started / job.succeeded / job.failed / job.canceled` 이벤트 → 상태 전환 시 갱신

**ASCII 스케치**

```
┌──────────────────────────────────────────────────────────┐
│ [← 목록으로]   job-0042   ● 진행중   [취소] [재시도]     │  ← Header + Actions
├──────────────────────────────────────────────────────────┤
│ 진행률:   ████████░░░░░░░░  67%   경과: 0:12             │  ← ProgressBar
├──────────────────────────────────────────────────────────┤
│ payload   { "type": "resize", "width": 1920 }            │
│ 우선순위  5    태그  [image] [resize]    워커  worker-02  │  ← MetadataTable
├──────────────────────────────────────────────────────────┤
│ 로그                                          [자동스크롤]│
│ 00:00:01  작업 시작                                       │
│ 00:00:03  이미지 로드 완료 (2.3MB)                        │
│ 00:00:11  리사이즈 처리 중 (67%)                          │  ← LogViewer (스트리밍)
│ ▌ (커서 — 실시간 수신 중)                                 │
└──────────────────────────────────────────────────────────┘
```

---

### 화면 5 — 빈 상태 (Empty State)

**목적.** 큐에 작업이 없을 때, 또는 필터 결과가 0건일 때 안내 및 다음 행동 유도.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `EmptyState` | 아이콘 + 타이틀 + 설명 + CTA | `job.submitted` 수신 시 자동 해제 |

**변형.**
- `EmptyState[variant=no-jobs]` — 큐 자체가 비어있음
- `EmptyState[variant=no-results]` — 필터 결과 0건 (필터 초기화 CTA)

**ASCII 스케치**

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                  ○ (아이콘: 빈 받침대)                    │
│                                                          │
│                   작업이 없습니다                         │
│            새 작업을 제출하면 여기에 표시됩니다.           │
│                                                          │
│              [ + 새 작업 제출하기 ]                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

### 화면 6 — 오류 상태 (Error State)

**목적.** API 연결 실패, SSE 연결 끊김, 서버 500 등 시스템 레벨 오류 안내.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `SSEConnectionBanner` | 연결 끊김 배너 (상단 고정, 재연결 시도 카운트) | SSE `onerror` → 배너 표시; 재연결 성공 → 숨김 |
| `ErrorState` | 전체 페이지 오류 (API 불가 등) | — |
| `Button[ghost]` — 재시도 | 수동 재요청 | — |

**배너 vs 전체 페이지 기준.**
- SSE 연결 끊김 → 배너 (데이터는 마지막 상태 표시, 자동 재연결 시도)
- API 완전 불가(모든 fetch 실패) → 전체 페이지 오류 상태

**ASCII 스케치 — SSE 배너**

```
┌──────────────────────────────────────────────────────────┐
│ ⚠ 실시간 연결이 끊겼습니다. 재연결 중… (3회 시도)  [닫기] │  ← SSEConnectionBanner
├──────────────────────────────────────────────────────────┤
│ (기존 화면 흐리게 표시)                                   │
└──────────────────────────────────────────────────────────┘
```

---

### 화면 7 — 토스트/알림 (Toast / Notification)

**목적.** 작업 완료·실패·취소 이벤트를 사용자에게 즉시 비침입적으로 알림.

**핵심 컴포넌트**

| 컴포넌트 | 역할 | SSE 바인딩 |
|---|---|---|
| `Toast` | 단일 알림 칩 (success/error/warning/info) | SSE `job.succeeded`, `job.failed` → 생성 |
| `ToastQueue` | 최대 3개 동시, FIFO 관리 | — |
| `ToastRegion` | `aria-live` 컨테이너 (a11y) | — |

**실시간 바인딩.** SSE `job.succeeded` → success 토스트. SSE `job.failed` → error 토스트. SSE 재연결 성공 → info 토스트.

**ASCII 스케치**

```
                              ┌──────────────────────────┐
                              │ ✓ job-0041 완료됨.  [×]  │  ← Toast[success]
                              ├──────────────────────────┤
                              │ ✕ job-0040 실패.   [×]  │  ← Toast[error]
                              └──────────────────────────┘
                                        (우하단 고정)
```

---

## 2. 디자인 방향 후보

> **금지.** "clean minimal", 기본 Tailwind/shadcn 템플릿, 중앙 정렬 히어로, 균일 카드 그리드.

### 후보 A — Dark Command Center (추천)

**키워드.** `operational`, `high-density`, `signal-driven`

실시간 모니터링 도구의 특성에 직접 대응. 어두운 배경 위에 상태 색(amber/blue/green/red)이 신호처럼 부각. 장시간 주시에 유리. Linear, Vercel Dashboard, Grafana의 운영자 UX 계보.

- 배경: oklch 12~17% 채도 극소 (차콜-블루)
- 강조: OKLCH 고채도 상태 색 4종
- 타이포: 모노스페이스 포인트(로그·ID) + 산세리프 계층(라벨·헤딩)
- 레이아웃: 상단 상태 카드 행 + 아래 전체폭 리스트, 드라마틱한 여백 최소화 (정보 밀도 우선)

### 후보 B — Swiss System UI

**키워드.** `structured`, `typographic`, `enterprise`

명확한 그리드, 굵은 타이포그래피 위계, 라이트 모드 기본. GitHub·Stripe Dashboard 계보. 정보 밀도를 그리드 규율로 해결.

- 배경: oklch 98% 라이트 기본 (다크 선택적)
- 강조: 단일 액센트 컬러 (인디고 계열)
- 타이포: Inter/Geist, 강한 크기 대비 (헤딩 vs 바디)
- 레이아웃: 12컬럼 그리드, 테이블 중심, 사이드바 없음

### 후보 C — Functional Neo-Brutalism

**키워드.** `raw`, `high-contrast`, `developer-tool`

두꺼운 테두리, 강한 블록 구분, 개발 도구 느낌. Railway, Fly.io 계보. 상태 배지가 강렬한 배경 블록으로 표현.

- 배경: oklch 97% + 1px 블랙 보더
- 강조: 채도 높은 상태 배경 블록
- 타이포: 굵은 산세리프, 균일 크기
- 레이아웃: 블록 기반, 명확한 경계선

### 추천 및 이유

**→ 후보 A (Dark Command Center) 채택 권장.**

실시간 작업 큐는 운영·모니터링 도구. 사용자는 대기/진행/완료/실패 상태를 빠르게 스캔한다. 어두운 배경에서 상태 색이 가장 선명하게 구분되고, 장시간 주시 시 눈의 피로가 적다. 라이트 모드는 토큰으로 지원하되 다크를 기본값으로.

---

## 3. 디자인 토큰 1차 — 요약

> 전체 CSS 변수 명세는 [ui-tokens.md](./ui-tokens.md) 참조.

**색상 팔레트 (OKLCH)**

| 역할 | 다크 | 라이트 |
|---|---|---|
| `--color-surface` | oklch(12% 0.007 250) | oklch(98% 0 0) |
| `--color-surface-elevated` | oklch(17% 0.009 250) | oklch(100% 0 0) |
| `--color-text` | oklch(94% 0 0) | oklch(12% 0 0) |
| `--color-text-muted` | oklch(58% 0 0) | oklch(44% 0 0) |
| `--color-accent` | oklch(64% 0.20 250) | oklch(55% 0.20 250) |
| `--color-status-pending` | oklch(72% 0.14 85) | oklch(58% 0.14 85) |
| `--color-status-running` | oklch(64% 0.20 250) | oklch(55% 0.20 250) |
| `--color-status-done` | oklch(68% 0.18 150) | oklch(52% 0.18 150) |
| `--color-status-failed` | oklch(62% 0.22 25) | oklch(52% 0.22 25) |
| `--color-border` | oklch(25% 0.01 250) | oklch(88% 0 0) |

---

## 4. a11y 기준 (WCAG 2.2 AA)

### 4-1. 색 대비

| 요소 | 기준 | 대상 토큰 |
|---|---|---|
| 본문 텍스트 (≤18px 일반) | 4.5:1 이상 | `--color-text` vs `--color-surface` |
| 큰 텍스트 (≥18px 일반 / ≥14px bold) | 3:1 이상 | `--color-text` vs `--color-surface` |
| UI 컴포넌트 경계 (입력 테두리·버튼 외곽) | 3:1 이상 | `--color-border` vs `--color-surface` |
| StatusBadge 텍스트 vs 배지 배경 | 4.5:1 이상 | 각 `--color-status-*` 조합 |
| 포커스 링 | 3:1 이상 | `--color-focus-ring` vs 주변 배경 |

**색상에만 의존한 상태 표시 금지.** 모든 `StatusBadge`는 색 + 아이콘 + 텍스트 레이블 3종 병기.

### 4-2. 키보드 내비게이션 시나리오

| 시나리오 | 키 | 기대 동작 |
|---|---|---|
| 페이지 탐색 | `Tab` / `Shift+Tab` | 포커스가 논리적 순서로 이동 |
| 버튼 활성화 | `Enter` / `Space` | 버튼(재시도·취소·로그인) 실행 |
| 드롭다운/필터 열기 | `Enter` / `Space` | FilterBar 메뉴 열림 |
| 드롭다운 항목 선택 | `ArrowUp` / `ArrowDown` + `Enter` | 항목 이동 및 선택 |
| 모달/토스트 닫기 | `Escape` | 포커스 원위치 복귀 |
| JobCard 목록 탐색 | `ArrowUp` / `ArrowDown` (리스트박스 패턴) | 카드 간 이동 |
| 로그인 폼 제출 | `Enter` (이메일 또는 비밀번호 필드 내) | 폼 submit |

포커스 트랩.
- 모달, 드롭다운 오픈 시 포커스가 내부에 갇혀야 함.
- 닫기 후 트리거 요소로 포커스 복귀.

포커스 표시.
- 모든 인터랙티브 요소: `outline: 2px solid var(--color-focus-ring); outline-offset: 2px`
- 외곽선을 `outline: none` 으로 제거하지 않음. `focus-visible` 한정으로 표시.

### 4-3. 모션 감쇠 정책 (`prefers-reduced-motion`)

```
@media (prefers-reduced-motion: reduce) {
  모든 트랜지션 duration → 0ms 또는 1ms
  토스트 진입: translateX 슬라이드 제거 → opacity fade만 유지
  ProgressIndicator: transition 제거, 즉시 값 반영
  JobCard 삽입: 슬라이드 다운 제거 → 즉시 표시
  SSEConnectionBanner: 슬라이드 제거 → 즉시 표시
}
```

애니메이션이 정보 전달에 필요한 경우(진행률 변화)는 motion 제거 후에도 수치 텍스트로 동일 정보 제공.

### 4-4. SSE 푸시 알림 aria-live 처리

실시간 이벤트를 스크린리더가 적절히 읽을 수 있도록 라이브 리전을 구분.

| 이벤트 | 컴포넌트 | aria 처리 |
|---|---|---|
| 큐 카운트 변경 (`queue.counts`) | `QueueStatusCard` | `aria-live="polite"` — 현재 읽기 마친 후 전달 |
| 작업 완료 (`job.succeeded`) | `Toast[success]` | `role="status"` + `aria-live="polite"` |
| 작업 실패 (`job.failed`) | `Toast[error]` | `role="alert"` + `aria-live="assertive"` — 즉시 인터럽트 |
| SSE 연결 끊김 | `SSEConnectionBanner` | `role="alert"` + `aria-live="assertive"` |
| SSE 재연결 성공 | `Toast[info]` | `role="status"` + `aria-live="polite"` |
| 로그 라인 스트리밍 (`log_line`) | `LogViewer` | `aria-live="off"` — 읽지 않음 (연속 스트림은 노이즈) |
| 진행률 갱신 (`job.progress`) | `ProgressBar` | `aria-valuenow` 갱신 + `aria-label="진행률 {n}%"` |

`ToastRegion` 구현 참고.
```html
<!-- 모든 Toast를 담는 단일 라이브 리전 컨테이너 -->
<div
  id="toast-region"
  aria-label="알림"
  aria-live="polite"     <!-- 기본값; 개별 Toast가 role="alert"로 오버라이드 -->
  aria-atomic="false"    <!-- 각 Toast를 개별 발화 -->
>
  <!-- Toast 컴포넌트가 동적으로 삽입/제거됨 -->
</div>
```

`ProgressBar` 구현 참고.
```html
<div
  role="progressbar"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-valuenow="67"
  aria-label="job-0042 진행률 67%"
>
  <div class="progress-fill" style="width: 67%"></div>
</div>
```

---

## 5. 컴포넌트 우선순위 표

### M0 — 공통 기반 (M1 착수 전 필수)

| 컴포넌트 | 파일 경로 (예정) | 역할 |
|---|---|---|
| `Button` | `src/components/ui/Button.tsx` | variant: primary / ghost / destructive |
| `StatusBadge` | `src/components/ui/StatusBadge.tsx` | 상태 칩 (아이콘 + 색 + 텍스트) |
| `Input` | `src/components/ui/Input.tsx` | 텍스트·이메일 입력 |
| `PasswordInput` | `src/components/ui/PasswordInput.tsx` | visibility toggle |
| `PageLayout` | `src/components/layout/PageLayout.tsx` | 헤더 + 콘텐츠 영역 래퍼 |
| `AppHeader` | `src/components/layout/AppHeader.tsx` | 앱명 + 사용자 메뉴 |

### M1 — 구현 1순위

| 컴포넌트 | 파일 경로 (예정) | 의존 | 실시간 바인딩 |
|---|---|---|---|
| `QueueStatusCard` | `src/components/queue/QueueStatusCard.tsx` | `StatusBadge` | SSE `queue.counts` |
| `JobCard` | `src/components/jobs/JobCard.tsx` | `StatusBadge`, `ProgressIndicator`, `Button` | SSE `job.started / job.succeeded / job.failed / job.canceled` |
| `ProgressIndicator` | `src/components/ui/ProgressIndicator.tsx` | — | `aria-valuenow` 갱신 |
| `LoginForm` | `src/components/auth/LoginForm.tsx` | `Input`, `PasswordInput`, `Button`, `ErrorMessage` | — |

### M2 — 구현 2순위

| 컴포넌트 | 파일 경로 (예정) | 의존 | 실시간 바인딩 |
|---|---|---|---|
| `JobDetail` | `src/components/jobs/JobDetail.tsx` | `ProgressIndicator`, `StatusBadge`, `Button`, `LogViewer` | SSE `/events/jobs/{id}` |
| `LogViewer` | `src/components/jobs/LogViewer.tsx` | — | SSE `log_line` append |
| `Toast` / `ToastQueue` | `src/components/ui/Toast.tsx` | — | SSE `job.succeeded`, `job.failed` |
| `EmptyState` | `src/components/ui/EmptyState.tsx` | `Button` | SSE `job.submitted` → 해제 |
| `ErrorState` | `src/components/ui/ErrorState.tsx` | `Button` | — |
| `SSEConnectionBanner` | `src/components/ui/SSEConnectionBanner.tsx` | — | SSE `onerror` / 재연결 |
| `FilterBar` | `src/components/jobs/FilterBar.tsx` | — | — |

---

## 완료 확인 체크리스트

- [x] 화면 인벤토리 7개 (로그인·홈·리스트·상세·빈상태·오류·토스트) 목적·컴포넌트·실시간 바인딩 포함
- [x] 디자인 방향 후보 3개 + 추천 1개 이유 포함
- [x] 디자인 토큰 1차 요약 (전체는 ui-tokens.md)
- [x] a11y 기준: 색 대비 비율(WCAG AA), 키보드 시나리오, 모션 감쇠, SSE 라이브 리전
- [x] 컴포넌트 우선순위 표 (M0/M1/M2)
- [x] 마크업·구현 코드 없음 (분석/설계 단계)
