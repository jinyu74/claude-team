# Inspection: T2 — 수진 실시간 큐 스택 리서치 + 의존성 감사

- 검수일: 2026-05-19 13:36
- 검수자: CTO 제임스
- 발신자: 수진 (Researcher)
- 회신: `[결과] T2 리서치 완료. docs/analysis/research-realtime-stack.md, dependency-audit.md 참조.`
- 산출물:
  - `docs/analysis/research-realtime-stack.md` (278 lines)
  - `docs/analysis/dependency-audit.md` (113 lines)

## 5종 검수

| 항목 | 결과 | 비고 |
|---|---|---|
| (a) 스코프 충족 | ✅ | OSS 5건·라이브러리 4쌍·CVE 표·PoC 시나리오·위험 블로커 5건·최종 권장 요약 |
| (b) 형식 준수 | ✅ | 마크다운·표·코드블록·출처 URL+확인일 |
| (c) 누락 없음 | ✅ | 후보 라이브러리 전부 CVE 표 등재, 권고는 모두 한 줄 결론 |
| (d) 품질 기준 충족 | ✅ | 객관 근거(별점·릴리스·CVE) + 실행 가능 PoC 코드. **CVE-2025-49844 (CVSS 10.0) 식별이 핵심 성과** |
| (e) 후속 단계 정합 | ✅ | ADR-001 §2.4(Redis Stream 백필) 와 R-02(이벤트 유실) 상호 보완. R-04(Last-Event-ID) 는 ADR-001 §2.4 로 이미 해결됨 |

**판정: 통과 (PASS)**

## 강점

- **CVE-2025-49844 "RediShell"** (CVSS 10.0, Redis Lua UAF → 인증된 사용자 RCE) 발견. 시범에서도 운영 패턴 확립을 위해 즉시 차단해야 할 항목. R-006 으로 리스크 레지스터 등재.
- Flask-SSE 의 "저자 본인 운영 미사용 인정" 같은 1차 출처 기반 결론.
- PoC 시나리오가 단순 권고가 아니라 실행 가능한 셸 명령·Locust 파일·측정 항목 표 포함 → 카맥이 그대로 베이스라인에 활용 가능.
- SQLAlchemy 2.0 vs asyncpg 결론에서 "지연 차이(1.2ms vs 0.35ms) 가 API p95 200ms 목표에 무관한 수준" 이라는 의사결정 친화 분석.
- Redis 운영 설정 권고(`requirepass`, `bind 127.0.0.1`, `rename-command`) 가 마크 docker-compose 에 즉시 반영 가능한 형태.

## 발견된 작은 정합 이슈 (보강 안내)

- ADR-001 §4.2 Redis 키 정의에 **버전 요구사항(`redis:7.4.2` 이상)** 이 명시되어 있지 않음. 네이선 보강 시 추가 명시 권고. 마크 docker-compose 에서도 핀.

## 후속

- 수진: 통과 회신. 월간 CVE 재스캔 2026-06-19 (수진 routine 으로 등록).
- 네이선: 이미 진행 중인 ADR-001 §5.4 보강에 §4.2 Redis 버전 고정 한 줄 추가 부탁.
- 마크: 구현 시 `docker-compose.yml` 에 `redis:7.4.2` 이상 핀, 인증 + bind + rename-command 적용.
- 카맥: PoC 측정 항목 표를 perf 베이스라인 초안에 흡수.
