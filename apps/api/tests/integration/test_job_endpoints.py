# 작업 엔드포인트 통합 테스트 — 제출·조회·취소·재시도
import pytest
import uuid
from unittest.mock import patch


def login_user(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.get_json()["csrf_token"]


def make_user(app, email="jobs@example.com", password="pass-123"):
    from src.extensions import db
    from src.models.user import User
    from src.services.auth import hash_password

    with app.app_context():
        user = User(id=str(uuid.uuid4()), email=email, password_hash=hash_password(password))
        db.session.add(user)
        db.session.commit()
        return user.id


class TestJobSubmit:
    def test_submit_job_returns_201(self, client, app):
        make_user(app, "submit@example.com")
        csrf = login_user(client, "submit@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-task-id"
            resp = client.post(
                "/api/jobs",
                json={
                    "type": "dummy.sleep",
                    "payload": {"seconds": 5, "fail_prob": 0.0},
                    "priority": 0,
                },
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "key-submit-1"},
            )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "pending"
        assert "id" in data

    def test_submit_job_missing_type_returns_422(self, client, app):
        make_user(app, "validate@example.com")
        csrf = login_user(client, "validate@example.com", "pass-123")

        resp = client.post(
            "/api/jobs",
            json={"payload": {}},
            headers={"X-CSRF-Token": csrf, "Idempotency-Key": "key-val-1"},
        )
        assert resp.status_code == 422

    def test_submit_duplicate_idempotency_key_returns_same_job(self, client, app):
        make_user(app, "idem@example.com")
        csrf = login_user(client, "idem@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "celery-task-id"
            resp1 = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "unique-key-abc"},
            )
            resp2 = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "unique-key-abc"},
            )
        assert resp1.status_code == 201
        assert resp2.status_code == 200
        assert resp1.get_json()["id"] == resp2.get_json()["id"]

    def test_submit_without_auth_returns_401(self, client):
        resp = client.post(
            "/api/jobs",
            json={"type": "dummy.sleep", "payload": {}},
            headers={"Idempotency-Key": "key-noauth"},
        )
        assert resp.status_code == 401

    def test_submit_without_csrf_returns_403(self, client, app):
        make_user(app, "nocsrf@example.com")
        login_user(client, "nocsrf@example.com", "pass-123")

        resp = client.post(
            "/api/jobs",
            json={"type": "dummy.sleep", "payload": {}},
            headers={"Idempotency-Key": "key-nocsrf"},
        )
        assert resp.status_code == 403

    def test_submit_without_idempotency_key_returns_422(self, client, app):
        make_user(app, "noidkey@example.com")
        csrf = login_user(client, "noidkey@example.com", "pass-123")

        resp = client.post(
            "/api/jobs",
            json={"type": "dummy.sleep", "payload": {}},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 422


class TestJobList:
    def test_list_jobs_returns_paginated_results(self, client, app):
        make_user(app, "list@example.com")
        csrf = login_user(client, "list@example.com", "pass-123")

        resp = client.get("/api/jobs", headers={"X-CSRF-Token": csrf})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "total" in data

    def test_list_jobs_filters_by_status(self, client, app):
        make_user(app, "filter@example.com")
        csrf = login_user(client, "filter@example.com", "pass-123")

        resp = client.get("/api/jobs?status=pending", headers={"X-CSRF-Token": csrf})
        assert resp.status_code == 200

    def test_list_jobs_only_own_jobs(self, client, app):
        """사용자는 자신의 작업만 볼 수 있다."""
        make_user(app, "user-a@example.com")
        make_user(app, "user-b@example.com")
        csrf_a = login_user(client, "user-a@example.com", "pass-123")
        csrf_b = login_user(client, "user-b@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf_a, "Idempotency-Key": "key-a-1"},
            )

        resp_b = client.get("/api/jobs", headers={"X-CSRF-Token": csrf_b})
        assert resp_b.get_json()["total"] == 0


class TestJobDetail:
    def test_get_job_detail(self, client, app):
        make_user(app, "detail@example.com")
        csrf = login_user(client, "detail@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            create_resp = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "key-detail-1"},
            )
        job_id = create_resp.get_json()["id"]

        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == job_id

    def test_get_other_users_job_returns_404(self, client, app):
        make_user(app, "owner@example.com")
        make_user(app, "other@example.com")
        csrf_owner = login_user(client, "owner@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            create_resp = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf_owner, "Idempotency-Key": "key-owner-1"},
            )
        job_id = create_resp.get_json()["id"]

        # other 사용자로 owner의 job 조회
        login_user(client, "other@example.com", "pass-123")
        resp = client.get(f"/api/jobs/{job_id}")
        assert resp.status_code == 404


class TestJobCancel:
    def test_cancel_pending_job(self, client, app):
        make_user(app, "cancel@example.com")
        csrf = login_user(client, "cancel@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            create_resp = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "key-cancel-1"},
            )
        job_id = create_resp.get_json()["id"]

        with patch("src.blueprints.jobs.celery_app.control.revoke"):
            resp = client.patch(
                f"/api/jobs/{job_id}",
                json={"action": "cancel"},
                headers={"X-CSRF-Token": csrf},
            )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "canceled"

    def test_cancel_already_canceled_job_returns_409(self, client, app):
        from src.services.job import transition_job
        from src.models.job import Job

        make_user(app, "cancel2@example.com")
        csrf = login_user(client, "cancel2@example.com", "pass-123")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            create_resp = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": "key-cancel-2"},
            )
        job_id = create_resp.get_json()["id"]

        with app.app_context():
            job = Job.query.get(job_id)
            transition_job(job, "canceled")

        resp = client.patch(
            f"/api/jobs/{job_id}",
            json={"action": "cancel"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 409


class TestJobRetry:
    def _create_job(self, client, csrf, idempotency_key="key-retry-base"):
        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "t-id"
            resp = client.post(
                "/api/jobs",
                json={"type": "dummy.sleep", "payload": {"seconds": 1}, "priority": 0},
                headers={"X-CSRF-Token": csrf, "Idempotency-Key": idempotency_key},
            )
        return resp.get_json()["id"]

    def test_retry_failed_job_returns_new_job(self, client, app):
        from src.services.job import transition_job
        from src.models.job import Job

        make_user(app, "retry1@example.com")
        csrf = login_user(client, "retry1@example.com", "pass-123")
        job_id = self._create_job(client, csrf, "key-retry-1")

        with app.app_context():
            job = Job.query.get(job_id)
            transition_job(job, "running")
            job = Job.query.get(job_id)
            transition_job(job, "failed")

        with patch("src.blueprints.jobs.submit_job_task") as mock_task:
            mock_task.apply_async.return_value.id = "new-celery-id"
            resp = client.patch(
                f"/api/jobs/{job_id}",
                json={"action": "retry"},
                headers={"X-CSRF-Token": csrf},
            )
        assert resp.status_code == 201
        new_data = resp.get_json()
        assert new_data["id"] != job_id
        assert new_data["status"] == "pending"

    def test_retry_succeeded_job_returns_409(self, client, app):
        from src.services.job import transition_job
        from src.models.job import Job

        make_user(app, "retry2@example.com")
        csrf = login_user(client, "retry2@example.com", "pass-123")
        job_id = self._create_job(client, csrf, "key-retry-2")

        with app.app_context():
            job = Job.query.get(job_id)
            transition_job(job, "running")
            job = Job.query.get(job_id)
            transition_job(job, "succeeded")

        resp = client.patch(
            f"/api/jobs/{job_id}",
            json={"action": "retry"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "INVALID_TRANSITION"

    def test_retry_pending_job_returns_409(self, client, app):
        make_user(app, "retry3@example.com")
        csrf = login_user(client, "retry3@example.com", "pass-123")
        job_id = self._create_job(client, csrf, "key-retry-3")

        resp = client.patch(
            f"/api/jobs/{job_id}",
            json={"action": "retry"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "INVALID_TRANSITION"
