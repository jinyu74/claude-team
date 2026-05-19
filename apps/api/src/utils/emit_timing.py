# SSE 발행→수신 지연 측정 헬퍼 — ADR §5.4.3 Patch 2
import os
import time
from datetime import UTC, datetime

ENABLE_EMIT_AT: bool = os.getenv("ENABLE_EMIT_AT", "false").lower() == "true"


def maybe_add_emit_at(data: dict) -> dict:
    """ENABLE_EMIT_AT=true 일 때 _emit_at 타임스탬프를 데이터에 복사 주입한다."""
    if not ENABLE_EMIT_AT:
        return data
    # ADR §5.4.3: dict 포맷 — iso(문자열 파싱용) + monotonic_ns(정밀 측정용)
    emit_at = {"iso": datetime.now(UTC).isoformat(), "monotonic_ns": time.monotonic_ns()}
    return {**data, "_emit_at": emit_at}


def strip_internal_keys(
    data: dict,
    expose_emit_at: bool = False,
    channel: str = "user",
    is_test_client: bool = False,
) -> dict:
    """_ 접두사 키를 제거한다.
    _emit_at: is_test_client=True 시에만 Prometheus 기록 + 클라이언트 노출 (ADR §5.4.3)."""
    from src.utils.metrics import sse_emit_to_receive_seconds

    emit_at = data.get("_emit_at")
    if emit_at is not None and is_test_client:
        try:
            # ADR §5.4.3: iso 필드 파싱 후 지연 계산 (카맥 locustfile_sse_latency.py 매칭)
            iso_str = emit_at.get("iso") if isinstance(emit_at, dict) else None
            if iso_str:
                emit_ts = datetime.fromisoformat(iso_str).timestamp()
                latency = time.time() - emit_ts
                sse_emit_to_receive_seconds.labels(
                    channel=channel, client_type="test"
                ).observe(latency)
        except (ValueError, TypeError, AttributeError):
            pass

    result = {}
    for k, v in data.items():
        if k.startswith("_"):
            if expose_emit_at and k == "_emit_at":
                result[k] = v
        else:
            result[k] = v
    return result
