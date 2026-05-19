# 테스트 팩토리 — User, Job 모델 인스턴스 생성
import factory
from src.models.user import User
from src.services.auth import hash_password


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyFunction(lambda: hash_password("test-password-123"))


class JobFactory(factory.Factory):
    class Meta:
        from src.models.job import Job
        model = Job

    type = "dummy.sleep"
    payload = factory.LazyFunction(lambda: {"seconds": 5, "fail_prob": 0.0})
    priority = 0
    status = "pending"
    idempotency_key = factory.Sequence(lambda n: f"idem-key-{n}")
