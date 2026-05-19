# 리서치: 실시간 큐 스택 (Flask + Celery + Redis + SSE/WebSocket)

- 요청자: CTO 제임스 (T2)
- 수행: 수진 (Researcher)
- 작성일: 2026-05-19
- 확인일: 2026-05-19
- 상위 결정: [decisions/2026-05-19-realtime-task-queue-dashboard.md](../decisions/2026-05-19-realtime-task-queue-dashboard.md)

## 답할 질문

1. 채택하거나 포트할 수 있는 검증된 OSS 스켈레톤이 있는가?
2. SSE 구현은 Flask-SSE 라이브러리 vs 직접 구현 중 무엇이 낫는가?
3. WebSocket이 필요할 경우 Flask-Sock vs Flask-SocketIO 중 무엇인가?
4. Celery 모니터링은 Flower vs 커스텀 SSE 중 무엇인가?
5. PG ORM은 SQLAlchemy 2.0 vs raw asyncpg 중 무엇인가?

---

## 1. OSS 스켈레톤 평가 (5선)

> 검색 방법: `gh search repos`, GitHub Topics (`server-sent-events`, `celery-redis`, `flask-celery`), 웹 검색 병행.

| # | 저장소 | ★ | 라이선스 | 마지막 업데이트 | 요구사항 충족률 | 채택 권고 |
|---|---|---|---|---|---|---|
| 1 | [mher/flower](https://github.com/mher/flower) | 7,176 | BSD-3 | 2026-05-18 | 60% | **포트 권장** |
| 2 | [miguelgrinberg/Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) | 5,510 | MIT | 2026-05-18 | 40% | **참조(WebSocket 선택 시)** |
| 3 | [miguelgrinberg/flask-celery-example](https://github.com/miguelgrinberg/flask-celery-example) | 1,214 | MIT | 2026-04-27 | 75% | **포트 권장** |
| 4 | [singingwolfboy/flask-sse](https://github.com/singingwolfboy/flask-sse) | 323 | MIT | 2026-05-07 | 35% | **참조만** |
| 5 | [testdrivenio/flask-celery-project](https://github.com/testdrivenio/flask-celery-project) | 20 | 없음 | 2024-09-05 | 50% | **참조** |

### 세부 평가

**① mher/flower (★7,176, BSD-3, 2026-05-18)**
- 내용: Celery 분산 태스크 큐의 실시간 모니터링 웹 앱. WebSocket + HTTP API 혼용.
- 장점: 완성형 실시간 대시보드, 활발한 유지보수, Celery 공식 문서에서 권장.
- 단점: 범용 모니터링 도구라 UI 커스터마이징에 제약. 고부하(≥1k/hr 태스크) 환경에서 스케일 한계 보고됨.
- 충족률 산정 근거: 인증, 커스텀 UI(재시도/취소 버튼), payload 검증은 직접 구현해야 함.
- **권고: Flower의 이벤트 스트리밍 아키텍처를 패턴 참조. UI는 직접 구축.**

**② miguelgrinberg/Flask-SocketIO (★5,510, MIT, 2026-05-18)**
- 내용: Flask용 Socket.IO 통합. 양방향 실시간 통신.
- 장점: 활발한 유지보수(최신 릴리스 v5.6.1, 2026-02-21), 브라우저 폴백, 완성도 높음.
- 단점: SSE 채택 시 불필요. 의존성(eventlet 또는 gevent) 추가 필요.
- 충족률 산정: ADR-001 잠정안이 SSE이므로 현재 스코프와 불일치.
- **권고: WebSocket 선택 시 참조. SSE 확정 시 기각.**

**③ miguelgrinberg/flask-celery-example (★1,214, MIT, 2026-04-27)**
- 내용: Flask + Celery 기본 패턴. 작업 상태를 SSE 없이 폴링으로 조회하는 예제.
- 장점: 저자가 Flask/Celery 생태계 최고 권위자(Miguel Grinberg). 코드 품질 높음. 2026년까지 유지보수.
- 단점: SSE 미포함, 실시간 대시보드 UI 없음. 폴링 기반.
- 충족률 산정 근거: Flask+Celery 연동 패턴, 작업 상태 조회 API는 그대로 활용 가능.
- **권고: Celery 연동 기반 코드로 채택. SSE 레이어는 직접 추가.**

**④ singingwolfboy/flask-sse (★323, MIT, 코드 2026-05-07 / 릴리스 2021-01-10)**
- 내용: Flask용 SSE 라이브러리. Redis pub/sub 기반.
- 장점: SSE 구현 레퍼런스로 명확. MIT 라이선스.
- 단점: **마지막 PyPI 릴리스 v1.0.0이 2021년**. 저자 본인이 "실험적, 운영에서 미사용"이라 명시. `six` 의존성(Python 2 호환용) 포함.
- **권고: 참조만. 라이브러리 자체는 도입 금지.**

**⑤ testdrivenio/flask-celery-project (★20, 라이선스 없음, 2024-09-05)**
- 내용: TestDriven.io 블로그 튜토리얼용 프로젝트. Docker Compose, Flask, Celery 구성.
- 장점: 현대적인 Docker 구성(2024 업데이트). 실용적인 디렉터리 구조.
- 단점: 별점 낮음, 라이선스 없음(이식 시 법적 불명확), 실시간 스트리밍 미구현.
- **권고: Docker Compose 구성 참조. 코드 직접 채택은 라이선스 이슈로 보류.**

---

## 2. 핵심 라이브러리 비교표

### 2-A. SSE 구현: Flask-SSE vs 직접 구현

| 항목 | Flask-SSE | stream_with_context 직접 구현 |
|---|---|---|
| 최신 릴리스 | v1.0.0 (2021-01-10) | 해당 없음 (Flask 내장) |
| 유지보수 상태 | ⚠️ 사실상 중단 | ✅ Flask 자체와 함께 유지 |
| Redis 의존 | ✅ 필수 | ✅ 동일 (pub/sub 직접 구현) |
| 코드량 | 적음 | 50~100줄 추가 |
| 운영 경험 | 없음(저자 인정) | 풍부한 레퍼런스 |
| Gunicorn 호환 | gevent/eventlet 필요 | gevent/eventlet 필요 |
| 알려진 CVE | 없음 | 해당 없음 |
| **권장** | **거절** | **채택** |

- **근거**: Flask-SSE는 2021년 이후 릴리스 없음. 저자가 운영 미사용을 공개 인정. Redis pub/sub는 `redis-py`로 직접 구현해도 코드 50줄 수준이며 의존성 통제가 가능.

### 2-B. WebSocket: Flask-Sock vs Flask-SocketIO

| 항목 | Flask-Sock | Flask-SocketIO |
|---|---|---|
| 최신 릴리스 | v0.7.0 (2023-10-02) | v5.6.1 (2026-02-21) |
| GitHub ★ | 318 | 5,510 |
| 유지보수 상태 | ⚠️ 릴리스 정체 (2년 이상) | ✅ 활발 |
| 양방향 | ✅ 순수 WebSocket | ✅ Socket.IO 프로토콜 |
| 브라우저 폴백 | ✗ | ✅ 자동 |
| greenlet 불필요 | ✅ | ✗ (eventlet/gevent 필요) |
| 알려진 CVE | 없음 | CVE-2025-61765 (하위 의존성, §3 참조) |
| **권장** | **보류 (SSE 채택 시 불필요)** | **WebSocket 선택 시 채택** |

- **근거**: ADR-001 잠정안이 SSE이므로 WebSocket 라이브러리는 현재 불필요. 양방향이 필요한 취소 명령은 REST PATCH로 처리(결정서 §옵션평가 확정). WebSocket 전환이 결정되면 Flask-SocketIO 채택(유지보수 우위).

### 2-C. Celery 모니터링: Flower vs 커스텀 SSE

| 항목 | Flower | 커스텀 SSE |
|---|---|---|
| 최신 릴리스 | v2.0.1 (2023-08-13) | 해당 없음 |
| GitHub ★ | 7,176 | — |
| 구현 비용 | 낮음 (설치만) | 중간 (직접 개발) |
| 커스터마이징 | 제한적 | 완전 자유 |
| 고부하 스케일 | ⚠️ ≥1k/hr 태스크 시 제한 | 설계에 따라 다름 |
| 우리 UI 통합 | ✗ 별도 포트 | ✅ 대시보드와 통합 |
| **권장** | **개발 중 모니터링 도구로 채택** | **프로덕션 대시보드는 직접 구현** |

- **근거**: Flower는 개발/디버깅 단계에서 병렬 실행하여 Celery 상태를 빠르게 파악하는 용도. 사용자에게 보여주는 대시보드 UI는 커스텀 SSE로 별도 구현. 시범 프로젝트 규모(소규모 데모)에서 Flower 스케일 한계는 무관.

### 2-D. PG ORM: SQLAlchemy 2.0 vs raw asyncpg

| 항목 | SQLAlchemy 2.0 | raw asyncpg |
|---|---|---|
| 최신 릴리스 | 2.0.40 (2025년 초) | 0.30.x (2025년) |
| Flask 친화도 | ✅ Flask-SQLAlchemy, Alembic | ⚠️ Flask와 async 조합 복잡 |
| 마이그레이션 | Alembic (성숙) | 별도 도구 필요 |
| 쿼리 지연 (SELECT 10k) | 1.2ms avg | 0.35ms avg |
| asyncio 지원 | ✅ create_async_engine | ✅ 네이티브 |
| 알려진 CVE | 없음 (2024-2025) | 없음 |
| 학습 곡선 | 낮음 | 높음 |
| **권장** | **채택** | **보류** |

- **근거**: Flask는 동기 기반이며 asyncpg를 직접 사용하면 async 루프 관리가 복잡해짐. 성능 차이(1.2ms vs 0.35ms)는 API p95 목표(200ms)에 무관한 수준. SQLAlchemy 2.0 asyncio 확장을 통해 필요 시 async 쿼리도 가능.

---

## 3. CVE / 보안 감사

> 출처: GHSA, Tenable, Snyk, NVD. 확인일: 2026-05-19.

| 패키지 | CVE | 심각도 | 설명 | 영향 버전 | 픽스 버전 | 상태 |
|---|---|---|---|---|---|---|
| redis (서버) | CVE-2025-49844 "RediShell" | **CRITICAL (CVSS 10.0)** | Lua UAF → 인증된 사용자 RCE | < 7.4.x | 7.4.2 / 7.2.7 / 6.2.17 | ⚠️ 즉시 업그레이드 |
| redis (서버) | CVE-2024-46981 | **HIGH** | Lua 가비지컬렉터 조작 → RCE | < 7.4.2 | 7.4.2 / 7.2.7 | ⚠️ 픽스 포함 버전 사용 |
| redis (서버) | GHSA-r67f-p999-2gff | Medium | 미인증 클라이언트 출력 버퍼 무제한 증가 → DoS | 다수 | 7.2.x 최신 | 모니터링 권장 |
| python-socketio | CVE-2025-61765 | **HIGH** | Redis 메시지큐 통한 pickle 역직렬화 RCE | < 5.14.0 | 5.14.0 (JSON 인코딩으로 전환) | SSE 채택 시 미해당 |
| celery | CVE-2023-46215 | HIGH | Apache Airflow Celery 공급자 로그에 민감정보 노출 | Airflow 한정 | Airflow 패치 | celery 자체 무관 |
| flask-sse | 없음 | — | — | — | — | ✅ |
| flask-sock | 없음 | — | — | — | — | ✅ |
| SQLAlchemy | 없음 (2024-2025) | — | — | — | — | ✅ |
| Flask | 없음 (2024-2025) | — | — | — | — | ✅ |

### 조치 사항

1. **Redis 버전 고정**: `redis:7.4.2` 이상(Docker 이미지) 사용. CVE-2025-49844, CVE-2024-46981 모두 픽스됨.
2. **python-socketio 미채택**: SSE 확정 시 해당 라이브러리 의존성 없음. WebSocket 전환 시 v5.14.0 이상 고정.
3. **Celery CVE**: Celery 라이브러리 자체 CRITICAL/HIGH CVE 없음 (2024-2025 기준). Airflow 관련 CVE는 우리 스택과 무관.

---

## 4. 실시간 옵션 PoC 권장 시나리오 (SSE 검증)

> 목적: 네이선의 SSE 잠정안이 성능 목표(SSE 푸시 지연 p95 < 500ms, 1k 동시 연결)를 실제로 충족하는지 검증.

### 전제 환경

```bash
# 의존성 설치
pip install flask redis gunicorn gevent locust

# Redis 구동 (Docker)
docker run -d -p 6379:6379 redis:7.4.2
```

### 최소 SSE 서버 (검증용)

```python
# sse_poc.py — SSE PoC 검증용 최소 서버
import time, json
import redis
from flask import Flask, Response, stream_with_context

app = Flask(__name__)
r = redis.Redis()

@app.route("/stream")
def stream():
    def event_stream():
        pubsub = r.pubsub()
        pubsub.subscribe("task_events")
        for msg in pubsub.listen():
            if msg["type"] == "message":
                yield f"data: {msg['data'].decode()}\n\n"
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

@app.route("/push/<task_id>/<status>")
def push(task_id, status):
    r.publish("task_events", json.dumps({"task_id": task_id, "status": status}))
    return "ok"
```

```bash
# Gunicorn + gevent 워커로 구동
gunicorn -k gevent -w 4 --worker-connections 1000 sse_poc:app -b 0.0.0.0:5000
```

### 측정 시나리오 (Locust)

```python
# locustfile.py — 동시 연결 수·지연 측정
from locust import HttpUser, task
import time

class SSEUser(HttpUser):
    @task
    def connect_and_listen(self):
        start = time.time()
        with self.client.get("/stream", stream=True, catch_response=True) as r:
            for i, chunk in enumerate(r.iter_content(chunk_size=None)):
                latency_ms = (time.time() - start) * 1000
                if i == 0:
                    r.success()
                    print(f"첫 이벤트 지연: {latency_ms:.1f}ms")
                if i >= 5:
                    break
```

```bash
# 1k 동시 연결 부하 테스트
locust -f locustfile.py --headless -u 1000 -r 50 --host http://localhost:5000 --run-time 2m
```

### 측정 항목

| 항목 | 목표 | 측정 방법 |
|---|---|---|
| SSE 첫 이벤트 지연 | p95 < 500ms | Locust 타이밍 |
| 1k 연결 시 메모리 | < 2GB | `docker stats` 또는 `ps aux` |
| 연결 유지 시간 | 5분 이상 끊김 없음 | Locust 에러율 0% 확인 |
| 워커 CPU | < 80% | `top` / `htop` |

---

## 5. 위험 및 블로커

| ID | 유형 | 내용 | 심각도 | 해결 방향 |
|---|---|---|---|---|
| R-01 | 성능 | Gunicorn gevent 워커 수 × 연결 수 조합 최적화 필요. gevent 없이 SSE 불가 | 중 | PoC 시 워커 수 실험 (4→8→16) |
| R-02 | 운영 | Redis pub/sub는 구독자 없을 때 이벤트 유실. Celery 태스크 완료 시점에 구독자가 없으면 이벤트 손실 | 중 | 태스크 상태를 PG에도 기록, 재연결 시 REST API로 현재 상태 보완 조회 |
| R-03 | 보안 | Redis 7.4.2 미만 사용 시 CVE-2025-49844 (CVSS 10.0) 위험 | 높음 | Docker 이미지 redis:7.4.2 고정 필수 |
| R-04 | 미해결 질문 | SSE 재연결(EventSource 자동 재연결) 시 이전 이벤트 replay 필요한가? `Last-Event-ID` 구현 필요 여부 | 중 | 네이선 ADR-001에서 결정 요청 |
| R-05 | 미해결 질문 | Celery 워커와 Flask 앱이 같은 Redis pub/sub를 공유할 때 채널 네이밍 전략 | 저 | ADR-001에서 채널 스키마 정의 |

---

## 6. 최종 권장 요약

| 결정 항목 | 권장 | 근거 |
|---|---|---|
| SSE 구현 | stream_with_context 직접 구현 | Flask-SSE 유지보수 중단, 코드 50줄로 동일 기능 |
| WebSocket | 불필요 (SSE 채택 시) / Flask-SocketIO (전환 시) | ADR-001 잠정안 유지 |
| Celery 모니터링 | Flower (개발용) + 커스텀 SSE (대시보드) | 역할 분리 |
| PG ORM | SQLAlchemy 2.0 | Flask 친화, 성숙한 마이그레이션, 목표 지연과 무관 |
| Redis 버전 | 7.4.2 이상 고정 | CVE-2025-49844 픽스 |
| 스켈레톤 | flask-celery-example 기반 구축 | 코드 품질·유지보수 최우수 |

---

## 출처

- [mher/flower GitHub](https://github.com/mher/flower) (확인 2026-05-19)
- [miguelgrinberg/flask-celery-example](https://github.com/miguelgrinberg/flask-celery-example) (확인 2026-05-19)
- [singingwolfboy/flask-sse](https://github.com/singingwolfboy/flask-sse) (확인 2026-05-19)
- [miguelgrinberg/Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) (확인 2026-05-19)
- [testdrivenio/flask-celery-project](https://github.com/testdrivenio/flask-celery-project) (확인 2026-05-19)
- [Server-sent events in Flask without extra dependencies — Max Halford](https://maxhalford.github.io/blog/flask-sse-no-deps/) (확인 2026-05-19)
- [CVE-2025-49844 RediShell — Sysdig](https://www.sysdig.com/blog/cve-2025-49844-redishell) (확인 2026-05-19)
- [CVE-2025-61765 python-socketio — Tenable](https://www.tenable.com/cve/CVE-2025-61765) (확인 2026-05-19)
- [GHSA-4789-qfc9-5f9q Redis Lua UAF](https://github.com/redis/redis/security/advisories/GHSA-4789-qfc9-5f9q) (확인 2026-05-19)
- [Python + PostgreSQL SQLAlchemy vs asyncpg — dasroot.net](https://dasroot.net/posts/2026/02/python-postgresql-sqlalchemy-asyncpg-performance-comparison/) (확인 2026-05-19)
- [Flask-SSE PyPI](https://pypi.org/project/flask-sse/) (확인 2026-05-19)
- [Flask-Sock PyPI](https://pypi.org/project/flask-sock/) (확인 2026-05-19)
- [Flower PyPI](https://pypi.org/project/flower/) (확인 2026-05-19)
