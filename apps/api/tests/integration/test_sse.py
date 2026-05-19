# SSE 연결 통합 테스트 — 연결 수립·핑·인증 검증
import pytest
import uuid
from unittest.mock import patch, MagicMock


def make_user_and_login(client, app, email="sse@example.com"):
    from src.extensions import db
    from src.models.user import User
    from src.services.auth import hash_password

    with app.app_context():
        user = User(id=str(uuid.uuid4()), email=email, password_hash=hash_password("pass-123"))
        db.session.add(user)
        db.session.commit()

    resp = client.post("/api/auth/login", json={"email": email, "password": "pass-123"})
    return resp.get_json()["csrf_token"]


class TestSSEConnection:
    def test_sse_jobs_requires_auth(self, client):
        resp = client.get("/api/events/jobs")
        assert resp.status_code == 401

    def test_sse_jobs_returns_event_stream_content_type(self, client, app):
        csrf = make_user_and_login(client, app, "sse-ct@example.com")

        with patch("src.blueprints.events.subscribe_jobs_channel") as mock_sub:
            # 빈 제너레이터로 바로 종료
            mock_sub.return_value = iter([": ping\n\n"])
            resp = client.get("/api/events/jobs", headers={"X-CSRF-Token": csrf})

        assert "text/event-stream" in resp.content_type

    def test_sse_job_detail_requires_job_ownership(self, client, app):
        csrf = make_user_and_login(client, app, "sse-own@example.com")
        fake_job_id = str(uuid.uuid4())

        resp = client.get(f"/api/events/jobs/{fake_job_id}")
        assert resp.status_code in (401, 404)


class TestSSEBackfill:
    def test_last_event_id_header_triggers_backfill(self, client, app):
        """Last-Event-ID 헤더가 있으면 백필 로직이 호출된다."""
        csrf = make_user_and_login(client, app, "sse-bf@example.com")

        with patch("src.blueprints.events.backfill_from_stream") as mock_bf, \
             patch("src.blueprints.events.subscribe_jobs_channel") as mock_sub:
            mock_bf.return_value = iter([])
            mock_sub.return_value = iter([": ping\n\n"])

            client.get(
                "/api/events/jobs",
                headers={"X-CSRF-Token": csrf, "Last-Event-ID": "01HXYZ"},
            )

        mock_bf.assert_called_once()
