# 인증 엔드포인트 통합 테스트 — 로그인·로그아웃·세션


class TestLogin:
    def test_login_success(self, client, app):
        import uuid

        from src.extensions import db
        from src.models.user import User
        from src.services.auth import hash_password

        with app.app_context():
            user = User(
                id=str(uuid.uuid4()),
                email="test@example.com",
                password_hash=hash_password("secure-password-123"),
            )
            db.session.add(user)
            db.session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "secure-password-123"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "csrf_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert "password_hash" not in str(data)

    def test_login_sets_sid_cookie(self, client, app):
        import uuid

        from src.extensions import db
        from src.models.user import User
        from src.services.auth import hash_password

        with app.app_context():
            user = User(
                id=str(uuid.uuid4()),
                email="cookie@example.com",
                password_hash=hash_password("secure-password-123"),
            )
            db.session.add(user)
            db.session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"email": "cookie@example.com", "password": "secure-password-123"},
        )
        assert "sid" in resp.headers.get("Set-Cookie", "")

    def test_login_wrong_password(self, client, app):
        import uuid

        from src.extensions import db
        from src.models.user import User
        from src.services.auth import hash_password

        with app.app_context():
            user = User(
                id=str(uuid.uuid4()),
                email="fail@example.com",
                password_hash=hash_password("correct-password"),
            )
            db.session.add(user)
            db.session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"email": "fail@example.com", "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "any-password"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={"email": "test@example.com"})
        assert resp.status_code == 422


class TestLogout:
    def test_logout_clears_session(self, client, app):
        import uuid

        from src.extensions import db
        from src.models.user import User
        from src.services.auth import hash_password

        with app.app_context():
            user = User(
                id=str(uuid.uuid4()),
                email="logout@example.com",
                password_hash=hash_password("pass-123"),
            )
            db.session.add(user)
            db.session.commit()

        login_resp = client.post(
            "/api/auth/login",
            json={"email": "logout@example.com", "password": "pass-123"},
        )
        csrf_token = login_resp.get_json()["csrf_token"]

        logout_resp = client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert logout_resp.status_code == 204

        me_resp = client.get("/api/me")
        assert me_resp.status_code == 401

    def test_logout_without_session_returns_401(self, client):
        resp = client.post("/api/auth/logout", headers={"X-CSRF-Token": "any"})
        assert resp.status_code == 401


class TestMe:
    def test_me_returns_current_user(self, client, app):
        import uuid

        from src.extensions import db
        from src.models.user import User
        from src.services.auth import hash_password

        with app.app_context():
            user = User(
                id=str(uuid.uuid4()),
                email="me@example.com",
                password_hash=hash_password("pass-123"),
            )
            db.session.add(user)
            db.session.commit()

        client.post(
            "/api/auth/login",
            json={"email": "me@example.com", "password": "pass-123"},
        )
        resp = client.get("/api/me")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["email"] == "me@example.com"

    def test_me_without_auth_returns_401(self, client):
        resp = client.get("/api/me")
        assert resp.status_code == 401
