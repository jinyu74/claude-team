# dummy_sleep 워커 단위 테스트 — M7(상태 전이·job_events) + M8(error 마스킹)
from unittest.mock import MagicMock, call, patch

import pytest


@pytest.fixture
def mock_job():
    job = MagicMock()
    job.id = "job-aaa"
    job.user_id = "user-bbb"
    job.status = "pending"
    return job


@pytest.fixture
def task_self():
    """Celery Task bind=True 의 self 모의 객체."""
    ts = MagicMock()
    ts.request.retries = 0
    ts.max_retries = 3
    return ts


def _make_retry_exc():
    """self.retry() 가 raise 하는 예외 모의."""
    from celery.exceptions import Retry
    return Retry()


# ─── M7: 상태 전이 + job_events INSERT ────────────────────────────────────────

class TestStatusTransitions:
    def test_pending_to_running_to_succeeded(self, task_self, mock_job):
        """정상 경로: pending → running → succeeded, transition_job 2회 호출."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("src.worker.tasks.record_job_progress"),
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(task_self, job_id="job-aaa", user_id="user-bbb", seconds=1)

        assert mock_trans.call_args_list == [
            call(mock_job, "running"),
            call(mock_job, "succeeded"),
        ]

    def test_canceled_job_is_skipped(self, task_self, mock_job):
        """취소된 잡은 전이 없이 즉시 반환."""
        mock_job.status = "canceled"
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            result = dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1
            )

        mock_trans.assert_not_called()
        assert result == {"skipped": True}

    def test_missing_job_is_skipped(self, task_self):
        """DB에 없는 잡은 전이 없이 즉시 반환."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
        ):
            mock_db.session.get.return_value = None
            from src.worker.tasks import dummy_sleep
            result = dummy_sleep.run.__func__(
                task_self, job_id="no-such-job", user_id="u", seconds=1
            )

        mock_trans.assert_not_called()
        assert result == {"skipped": True}

    def test_fail_true_transitions_to_failed(self, task_self, mock_job):
        """fail=True: running → failed (PermanentError 즉시 실패)."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, fail=True
            )

        calls = mock_trans.call_args_list
        assert calls[0] == call(mock_job, "running")
        assert calls[1].args[1] == "failed"
        assert "error" in calls[1].kwargs

    def test_transient_retries_when_retries_remaining(self, task_self, mock_job):
        """transient=True, 재시도 남음 → self.retry() 호출, 상태는 failed 아님."""
        task_self.request.retries = 0
        retry_exc = _make_retry_exc()
        task_self.retry.side_effect = retry_exc

        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            with pytest.raises(type(retry_exc)):
                dummy_sleep.run.__func__(
                    task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, transient=True
                )

        task_self.retry.assert_called_once()
        # running 전이는 1번, failed 전이는 없어야 함
        statuses = [c.args[1] for c in mock_trans.call_args_list]
        assert "running" in statuses
        assert "failed" not in statuses

    def test_transient_exhausted_transitions_to_failed(self, task_self, mock_job):
        """transient=True, 재시도 소진(retries==max_retries) → failed 전이."""
        task_self.request.retries = 3  # max_retries = 3

        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, transient=True
            )

        task_self.retry.assert_not_called()
        statuses = [c.args[1] for c in mock_trans.call_args_list]
        assert statuses[-1] == "failed"

    def test_retry_countdown_follows_exponential_backoff(self, task_self, mock_job):
        """재시도 카운트다운이 base * 4^retry 공식을 따른다."""
        task_self.request.retries = 1
        retry_exc = _make_retry_exc()
        task_self.retry.side_effect = retry_exc

        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job"),
            patch("src.worker.tasks.os") as mock_os,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            mock_os.environ.get.return_value = "1"  # base = 1s
            from src.worker.tasks import dummy_sleep
            with pytest.raises(type(retry_exc)):
                dummy_sleep.run.__func__(
                    task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, transient=True
                )

        # retries=1 → countdown = 1 * 4^1 = 4.0
        _, kwargs = task_self.retry.call_args
        assert kwargs["countdown"] == pytest.approx(4.0)


# ─── M7: progress 이벤트 ────────────────────────────────────────────────────

class TestProgressEvents:
    def test_progress_events_emitted_in_order(self, task_self, mock_job):
        """progress 배열 순서대로 record_job_progress 호출."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job"),
            patch("src.worker.tasks.record_job_progress") as mock_prog,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self,
                job_id="job-aaa",
                user_id="user-bbb",
                seconds=3,
                progress=[0.33, 0.66],
            )

        assert mock_prog.call_count == 2
        assert mock_prog.call_args_list[0] == call(mock_job, "user-bbb", 0.33)
        assert mock_prog.call_args_list[1] == call(mock_job, "user-bbb", 0.66)

    def test_no_progress_events_when_none(self, task_self, mock_job):
        """progress 없으면 record_job_progress 미호출."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job"),
            patch("src.worker.tasks.record_job_progress") as mock_prog,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(task_self, job_id="job-aaa", user_id="user-bbb", seconds=2)

        mock_prog.assert_not_called()


# ─── M8: error 마스킹 ──────────────────────────────────────────────────────

class TestErrorMasking:
    def test_error_message_truncated_to_200_chars(self, task_self, mock_job):
        """error.message 는 200자를 초과할 수 없다."""
        long_msg = "x" * 300
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job"),
            patch("src.worker.tasks.PermanentError", side_effect=Exception(long_msg)),
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            # fail=True 인데 PermanentError 를 직접 mock 하기 어려우므로
            # _mask 함수만 직접 검증
            from src.worker.tasks import _mask
            result = _mask(long_msg)

        assert len(result) <= 200

    def test_failed_error_stored_is_masked(self, task_self, mock_job):
        """fail=True 시 transition_job 에 전달되는 error 값이 200자 이내."""
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, fail=True
            )

        failed_call = next(c for c in mock_trans.call_args_list if c.args[1] == "failed")
        if len(failed_call.args) > 2:
            error_val = failed_call.kwargs.get("error") or failed_call.args[2]
        else:
            error_val = failed_call.kwargs.get("error")
        assert error_val is not None
        assert len(error_val) <= 200

    def test_no_stack_trace_in_error(self, task_self, mock_job):
        """error 값에 Traceback / stack trace 패턴 미포함."""
        leak_patterns = ("Traceback", "/Users/", "/home/", "File \"")
        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            mock_job.status = "pending"
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, fail=True
            )

        for c in mock_trans.call_args_list:
            if c.args[1] == "failed":
                err = c.kwargs.get("error", "")
                for pattern in leak_patterns:
                    assert pattern not in err, f"leak pattern '{pattern}' in error: {err!r}"

    def test_transient_exhausted_error_is_short(self, task_self, mock_job):
        """재시도 소진 후 error 가 사람이 읽을 수 있는 짧은 메시지."""
        task_self.request.retries = 3

        with (
            patch("src.worker.tasks.db") as mock_db,
            patch("src.worker.tasks.transition_job") as mock_trans,
            patch("time.sleep"),
        ):
            mock_db.session.get.return_value = mock_job
            from src.worker.tasks import dummy_sleep
            dummy_sleep.run.__func__(
                task_self, job_id="job-aaa", user_id="user-bbb", seconds=1, transient=True
            )

        failed_call = next(c for c in mock_trans.call_args_list if c.args[1] == "failed")
        error_val = failed_call.kwargs.get("error")
        assert error_val is not None
        assert len(error_val) <= 50  # 사용자용 짧은 문구
