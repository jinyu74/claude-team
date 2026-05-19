# emit_timing 헬퍼 단위 테스트 — ADR §5.4.3 Patch 2
from datetime import UTC, datetime, timedelta
from unittest.mock import patch


class TestMaybeAddEmitAt:
    def test_adds_emit_at_when_enabled(self):
        # Arrange
        import src.utils.emit_timing as et
        data = {"status": "running"}

        # Act
        with patch.object(et, "ENABLE_EMIT_AT", True):
            result = et.maybe_add_emit_at(data)

        # Assert — ADR §5.4.3: dict 포맷 {iso, monotonic_ns}
        assert "_emit_at" in result
        emit_at = result["_emit_at"]
        assert isinstance(emit_at, dict)
        assert "iso" in emit_at and "monotonic_ns" in emit_at
        parsed = datetime.fromisoformat(emit_at["iso"])
        assert abs((datetime.now(UTC) - parsed).total_seconds()) < 1.0
        assert result["status"] == "running"
        assert data is not result  # 원본 불변

    def test_noop_when_disabled(self):
        # Arrange
        import src.utils.emit_timing as et
        data = {"status": "running"}

        # Act
        with patch.object(et, "ENABLE_EMIT_AT", False):
            result = et.maybe_add_emit_at(data)

        # Assert
        assert result is data
        assert "_emit_at" not in result


class TestStripInternalKeys:
    def test_strips_underscore_keys_and_records_latency_for_test_client(self):
        # Arrange — ADR §5.4.3: _emit_at 은 dict {iso, monotonic_ns}
        import src.utils.emit_timing as et
        past_iso = (datetime.now(UTC) - timedelta(milliseconds=50)).isoformat()
        emit_at = {"iso": past_iso, "monotonic_ns": 0}
        data = {"status": "done", "_emit_at": emit_at, "_internal": "x"}

        observed = []

        def fake_observe(v):
            observed.append(v)

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            mock_hist.labels.return_value.observe.side_effect = fake_observe
            result = et.strip_internal_keys(data, channel="user", is_test_client=True)

        # Assert
        assert "status" in result
        assert "_emit_at" not in result
        assert "_internal" not in result
        mock_hist.labels.assert_called_once_with(channel="user", client_type="test")
        assert len(observed) == 1
        assert observed[0] >= 0.04  # 최소 40ms 지연

    def test_no_latency_recorded_for_non_test_client(self):
        # Arrange
        import src.utils.emit_timing as et
        past_iso = (datetime.now(UTC) - timedelta(milliseconds=50)).isoformat()
        data = {"status": "done", "_emit_at": {"iso": past_iso, "monotonic_ns": 0}}

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            result = et.strip_internal_keys(data, is_test_client=False)

        # Assert
        assert "status" in result
        assert "_emit_at" not in result
        mock_hist.labels.assert_not_called()

    def test_no_latency_recorded_without_emit_at(self):
        # Arrange
        import src.utils.emit_timing as et
        data = {"status": "pending"}

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            result = et.strip_internal_keys(data, is_test_client=True)

        # Assert
        assert result == {"status": "pending"}
        mock_hist.labels.assert_not_called()

    def test_expose_emit_at_included_when_flag_true(self):
        # Arrange — M1: expose_emit_at=True + is_test_client=True 경로 (emit_timing.py:45-46)
        import src.utils.emit_timing as et
        past_iso = (datetime.now(UTC) - timedelta(milliseconds=30)).isoformat()
        emit_at_dict = {"iso": past_iso, "monotonic_ns": 0}
        data = {"status": "done", "_emit_at": emit_at_dict}

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            mock_hist.labels.return_value.observe.return_value = None
            result = et.strip_internal_keys(
                data, expose_emit_at=True, channel="job", is_test_client=True
            )

        # Assert — _emit_at 클라이언트 노출 + latency 기록 모두
        assert "_emit_at" in result
        assert result["_emit_at"] == emit_at_dict
        assert result["status"] == "done"
        mock_hist.labels.assert_called_once_with(channel="job", client_type="test")
