# 로컬/CI 개발용 시드 사용자 삽입 — E2E 픽스처와 동일한 계정 사용
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app import create_app
from src.extensions import db
from src.models.user import User
from src.services.auth import hash_password

SEED_USERS = [
    {"email": "e2e-admin@test.local", "password": "Test1234!"},
    {"email": "e2e-user@test.local", "password": "Test1234!"},
]


def seed() -> None:
    app = create_app()
    with app.app_context():
        created = 0
        for spec in SEED_USERS:
            if db.session.query(User).filter_by(email=spec["email"]).first():
                print(f"skip (exists): {spec['email']}")
                continue
            user = User(email=spec["email"], password_hash=hash_password(spec["password"]))
            db.session.add(user)
            created += 1
            print(f"created: {spec['email']}")
        db.session.commit()
        print(f"seed complete — {created} created, {len(SEED_USERS) - created} skipped")


if __name__ == "__main__":
    seed()
