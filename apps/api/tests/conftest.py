# 테스트 공통 픽스처 — Flask 앱, DB, Redis 목 설정
import os
import pytest
import fakeredis
import src.extensions as _ext

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("FLASK_ENV", "testing")


@pytest.fixture(scope="session")
def fake_redis_server():
    """세션 범위 fakeredis 서버 — pub/sub 포함."""
    server = fakeredis.FakeServer()
    return server


@pytest.fixture()
def fake_redis(fake_redis_server):
    """테스트별 fakeredis 클라이언트."""
    client = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)
    yield client
    client.flushdb()


@pytest.fixture()
def app(fake_redis):
    from src.app import create_app

    # create_app 호출 후 _redis_client 교체 — init_redis가 덮어쓰므로 이후에 설정
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "REDIS_URL": "redis://localhost:6379/0",
            "WTF_CSRF_ENABLED": False,
        }
    )
    _ext._redis_client = fake_redis

    with application.app_context():
        from src.extensions import db
        db.create_all()
        yield application
        db.drop_all()

    _ext._redis_client = None


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client, app):
    """로그인 후 세션 쿠키 + CSRF 헤더 반환."""
    from src.extensions import db
    from src.models.user import User
    from src.services.auth import hash_password
    import uuid

    with app.app_context():
        user = User(
            id=str(uuid.uuid4()),
            email="authheader@example.com",
            password_hash=hash_password("test-password-123"),
        )
        db.session.add(user)
        db.session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "authheader@example.com", "password": "test-password-123"},
    )
    assert resp.status_code == 200
    csrf_token = resp.get_json()["csrf_token"]
    return {"X-CSRF-Token": csrf_token}
