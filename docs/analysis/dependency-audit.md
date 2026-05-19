# Dependency Audit — 실시간 큐 대시보드 스택

- 최종 갱신: 2026-05-19 by 수진
- 도구: GitHub Advisory Database, Tenable, Snyk, NVD, OSV
- 확인일: 2026-05-19
- 다음 CVE 재스캔 예정: **2026-06-19** (수진)
- 관련 리서치: [research-realtime-stack.md](./research-realtime-stack.md)

## 1. 후보 의존성 현황

| 패키지 | 평가 버전 | 최신 버전 | 라이선스 | 사내 사용 | 상태 |
|---|---|---|---|---|---|
| Flask | 3.x | 3.1.x | BSD-3 | 없음 | ✅ 채택 예정 |
| Celery | 5.x | 5.6.x | BSD-3 | 없음 | ✅ 채택 예정 |
| redis-py | 5.x | 5.x | MIT | 없음 | ✅ 채택 예정 |
| SQLAlchemy | 2.0.x | 2.0.40 | MIT | 없음 | ✅ 채택 예정 |
| Flask-SocketIO | 5.x | 5.6.1 | MIT | 없음 | ⚠️ WebSocket 전환 시만 |
| python-socketio | 5.x | 5.14.0 | MIT | 없음 | ⚠️ WebSocket 전환 시만 |
| Flask-SSE | 1.0.0 | 1.0.0 | MIT | 없음 | ❌ 채택 금지 |
| Flask-Sock | 0.7.0 | 0.7.0 | MIT | 없음 | ⚠️ WebSocket 전환 시 재검토 |
| Flower | 2.0.1 | 2.0.1 | BSD-3 | 없음 | ✅ 개발 도구로 채택 |
| gunicorn | 22.x | 22.x | MIT | 없음 | ✅ 채택 예정 |
| gevent | 24.x | 24.x | MIT | 없음 | ✅ SSE 필수 |

---

## 2. CVE 표 (2024-05 ~ 2026-05, 최근 1년)

### CRITICAL

| CVE | 패키지 | CVSS | 설명 | 취약 버전 | 픽스 버전 | 대응 |
|---|---|---|---|---|---|---|
| CVE-2025-49844 "RediShell" | Redis (서버) | 10.0 | Lua 가비지컬렉터 UAF(Use-After-Free) → 인증된 사용자 RCE 가능. 인터넷 노출 인스턴스 수십만 개 영향. | < 7.4.2, < 7.2.7, < 6.2.17 | 7.4.2 / 7.2.7 / 6.2.17 | **즉시 업그레이드 필수. Docker 이미지 `redis:7.4.2` 고정.** |

### HIGH

| CVE | 패키지 | CVSS | 설명 | 취약 버전 | 픽스 버전 | 대응 |
|---|---|---|---|---|---|---|
| CVE-2024-46981 (GHSA-prpq-rh5h-46g9) | Redis (서버) | High | Lua 스크립트로 가비지컬렉터 조작 → RCE. CVE-2025-49844와 동일 계열. | < 7.4.2 | 7.4.2 | CVE-2025-49844 픽스에 포함 |
| CVE-2025-61765 (GHSA-g8c6-8fjj-2r4m) | python-socketio | High | Redis 메시지큐 통한 pickle 역직렬화 RCE. 멀티서버 배포 + Redis 메시지큐 환경에서만 발생. | < 5.14.0 | 5.14.0 (pickle → JSON 전환) | **SSE 채택 시 미해당. WebSocket 전환 시 v5.14.0 이상 필수.** |

### MEDIUM

| CVE | 패키지 | CVSS | 설명 | 취약 버전 | 픽스 버전 | 대응 |
|---|---|---|---|---|---|---|
| GHSA-r67f-p999-2gff | Redis (서버) | Medium | 미인증 클라이언트의 출력 버퍼 무제한 증가 → 메모리 소진 DoS | 다수 | 7.2.x 최신 | Redis 인증 활성화, 네트워크 격리로 완화 |
| CVE-2024-51741 (GHSA-39h2-x6c4-6w4c) | Redis (서버) | 4.4 | 잘못된 형식의 ACL 셀렉터 → DoS | 다수 | 7.4.2 | CVE-2025-49844 픽스에 포함 |

### 해당 없음 (최근 1년 CVE 없음)

| 패키지 | 비고 |
|---|---|
| Flask | 없음 |
| Celery | 자체 CVE 없음. CVE-2023-46215는 Apache Airflow 환경 한정, Celery 라이브러리 무관 |
| redis-py (클라이언트) | 없음 |
| SQLAlchemy | 없음 |
| Flask-SSE | 없음 (채택 금지 사유는 유지보수 중단, CVE 아님) |
| Flask-Sock | 없음 |
| gunicorn | 없음 |
| gevent | 없음 |

---

## 3. 조치 요약

### 즉시 필요

1. **Redis 버전 고정**: `redis:7.4.2` 이상 Docker 이미지 사용. `docker-compose.yml` 에 명시.
2. **Flask-SSE 채택 금지**: 의존성 목록에서 제거. stream_with_context 직접 구현으로 대체.
3. **python-socketio 버전 핀**: WebSocket 전환 결정 시 `python-socketio>=5.14.0` 명시.

### Redis 보안 설정 (운영 환경)

```bash
# Redis 인증 활성화 (GHSA-r67f-p999-2gff 완화)
requirepass <strong-password>

# 외부 바인딩 금지
bind 127.0.0.1

# 위험 명령어 비활성화
rename-command FLUSHALL ""
rename-command CONFIG ""
```

### 월간 CVE 스캔 항목

다음 패키지는 월간 재확인 대상.

- redis (서버 + 클라이언트)
- celery
- flask / werkzeug
- sqlalchemy
- python-socketio (WebSocket 전환 시)

---

## 4. 후속

- Redis 버전 고정 → 마크(T5 구현 시 docker-compose.yml 반영)
- python-socketio 버전 핀 여부 → 네이선 ADR-001 WebSocket 결정 후 확정
- 월간 CVE 재스캔 → 2026-06-19 (수진) — 결과를 본 문서 변경 이력에 추가

### 운영 진입 시 자동화 격상 권고 (backlog)

> 제임스 지시 2026-05-19. 별도 ADR 또는 Jira backlog 등재 대상.

1. **GitHub Actions monthly scheduled workflow** — `pip-audit` + `osv-scanner` 조합으로 의존성 전수 스캔 자동화
2. **Jira 티켓 자동 생성** — CRITICAL/HIGH 발견 시 Jira 이슈 자동 생성 + 정민·네이선 채널 알림 연동

현재는 세션 cron + 문서 앵커 방식으로 운영. 운영 환경 진입 결정 시 이 항목을 Sub-task로 분해한다.

---

## 출처

- [GHSA-4789-qfc9-5f9q Redis Lua UAF (RediShell)](https://github.com/redis/redis/security/advisories/GHSA-4789-qfc9-5f9q) (확인 2026-05-19)
- [CVE-2025-49844 RediShell 상세 — Sysdig](https://www.sysdig.com/blog/cve-2025-49844-redishell) (확인 2026-05-19)
- [CVE-2025-61765 python-socketio — Tenable](https://www.tenable.com/cve/CVE-2025-61765) (확인 2026-05-19)
- [GHSA-r67f-p999-2gff Redis DoS](https://github.com/redis/redis/security/advisories/GHSA-r67f-p999-2gff) (확인 2026-05-19)
- [Flask-SocketIO Snyk 보안 분석](https://snyk.io/advisor/python/flask-socketio) (확인 2026-05-19)
- [NVD CVE-2024-51741](https://nvd.nist.gov/vuln/detail/cve-2024-51741) (확인 2026-05-19)
