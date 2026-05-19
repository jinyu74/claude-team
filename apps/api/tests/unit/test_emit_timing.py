# emit_timing 헬퍼 단위 테스트 — ADR §5.4.3 Patch 2
import time
from unittest.mock import patch


class TestMaybeAddEmitAt:
    def test_adds_emit_at_when_enabled(self):
        # Arrange
        import src.utils.emit_timing as et
        data = {"status": "running"}

        # Act
        with patch.object(et, "ENABLE_EMIT_AT", True):
            result = et.maybe_add_emit_at(data)

        # Assert
        assert "_emit_at" in result
        assert abs(result["_emit_at"] - time.time()) < 1.0
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
    def test_strips_underscore_keys_and_records_latency(self):
        # Arrange
        import src.utils.emit_timing as et
        past = time.time() - 0.05
        data = {"status": "done", "_emit_at": past, "_internal": "x"}

        observed = []

        def fake_observe(v):
            observed.append(v)

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            mock_hist.observe.side_effect = fake_observe
            result = et.strip_internal_keys(data)

        # Assert
        assert "status" in result
        assert "_emit_at" not in result
        assert "_internal" not in result
        assert len(observed) == 1
        assert observed[0] >= 0.04  # 최소 40ms 지연

    def test_no_latency_recorded_without_emit_at(self):
        # Arrange
        import src.utils.emit_timing as et
        data = {"status": "pending"}

        with patch("src.utils.metrics.sse_emit_to_receive_seconds") as mock_hist:
            result = et.strip_internal_keys(data)

        # Assert
        assert result == {"status": "pending"}
        mock_hist.observe.assert_not_called()
