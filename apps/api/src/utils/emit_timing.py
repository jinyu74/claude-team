# SSE 발행→수신 지연 측정 헬퍼 — ADR §5.4.3 Patch 2
import os
import time

ENABLE_EMIT_AT: bool = os.getenv("ENABLE_EMIT_AT", "false").lower() == "true"


def maybe_add_emit_at(data: dict) -> dict:
    """ENABLE_EMIT_AT=true 일 때 _emit_at 타임스탬프를 데이터에 복사 주입한다."""
    if not ENABLE_EMIT_AT:
        return data
    return {**data, "_emit_at": time.time()}


def strip_internal_keys(data: dict, expose_emit_at: bool = False) -> dict:
    """_ 접두사 키를 제거한다.
    _emit_at: 항상 지연 측정에 사용. expose_emit_at=True (ENABLE_EMIT_AT + X-Perf-Client: test) 시에만 클라이언트에 노출."""
    from src.utils.metrics import sse_emit_to_receive_seconds

    emit_at = data.get("_emit_at")
    if emit_at is not None:
        try:
            latency = time.time() - float(emit_at)
            sse_emit_to_receive_seconds.observe(latency)
        except (ValueError, TypeError):
            pass

    result = {}
    for k, v in data.items():
        if k.startswith("_"):
            if expose_emit_at and k == "_emit_at":
                result[k] = v
        else:
            result[k] = v
    return result
