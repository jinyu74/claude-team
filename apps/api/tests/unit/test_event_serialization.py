# 이벤트 직렬화 단위 테스트 — SSE 포맷 검증
import json


class TestEventSerialization:
    def test_format_sse_event_with_type(self):
        from src.services.sse import format_sse_event
        result = format_sse_event(event_type="job.started", data={"job_id": "abc"})
        assert "event: job.started\n" in result
        assert "data:" in result
        assert result.endswith("\n\n")

    def test_format_sse_event_with_id(self):
        from src.services.sse import format_sse_event
        result = format_sse_event(
            event_type="job.done", data={"status": "succeeded"}, event_id="01HXYZ"
        )
        assert "id: 01HXYZ\n" in result

    def test_format_sse_event_data_is_valid_json(self):
        from src.services.sse import format_sse_event
        payload = {"job_id": "abc", "progress": 42}
        result = format_sse_event(event_type="job.progress", data=payload)
        # data: 행 이후 JSON 파싱 가능해야 함
        for line in result.splitlines():
            if line.startswith("data:"):
                json.loads(line[5:].strip())
                break

    def test_format_keepalive(self):
        from src.services.sse import format_keepalive
        result = format_keepalive()
        assert result == ": ping\n\n"
