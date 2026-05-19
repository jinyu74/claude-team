# Prometheus 메트릭 정의 — ADR §7.2 카탈로그 전부
from prometheus_client import Counter, Histogram, Gauge

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP 요청 처리 시간",
    ["method", "route", "status_code"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)

http_requests_total = Counter(
    "http_requests_total",
    "HTTP 요청 총 수",
    ["method", "route", "status_code"],
)

job_queue_length = Gauge(
    "job_queue_length",
    "현재 큐 길이 (상태별)",
    ["status"],
)

job_duration = Histogram(
    "job_duration_seconds",
    "작업 처리 시간",
    ["type", "status"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

job_outcomes_total = Counter(
    "job_outcomes_total",
    "작업 결과 총 수",
    ["type", "status"],
)

sse_clients_active = Gauge(
    "sse_clients_active",
    "현재 활성 SSE 클라이언트 수",
)

sse_messages_sent_total = Counter(
    "sse_messages_sent_total",
    "SSE 메시지 전송 총 수",
    ["event_type"],
)

sse_emit_to_receive_seconds = Histogram(
    "sse_emit_to_receive_seconds",
    "SSE 발행→수신 지연 시간 (ENABLE_EMIT_AT=true 시에만 기록)",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

queue_emitter_leader = Gauge(
    "queue_emitter_leader",
    "단일 리더 락 보유 여부 (1=보유, 0=미보유)",
)
