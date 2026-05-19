# 작업·이벤트 모델 — ADR §4.1 jobs / job_events 테이블
import uuid
from datetime import UTC, datetime

from src.extensions import db

JOB_STATUSES = ("pending", "running", "succeeded", "failed", "canceled")


class Job(db.Model):
    __tablename__ = "jobs"

    id: str = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: str = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type: str = db.Column(db.Text, nullable=False)
    payload: dict = db.Column(db.JSON, nullable=False, default=dict)
    priority: int = db.Column(db.SmallInteger, nullable=False, default=0)
    status: str = db.Column(
        db.Text,
        nullable=False,
        default="pending",
    )
    attempts: int = db.Column(db.SmallInteger, nullable=False, default=0)
    idempotency_key: str = db.Column(db.Text, nullable=False)
    celery_task_id: str | None = db.Column(db.Text, nullable=True)
    error: str | None = db.Column(db.Text, nullable=True)
    retried_to_job_id: str | None = db.Column(
        db.String(36), db.ForeignKey("jobs.id"), nullable=True
    )
    created_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    started_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_at: datetime | None = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "idempotency_key", name="uq_jobs_user_idem"),
        db.CheckConstraint(
            f"status IN {JOB_STATUSES}", name="ck_jobs_status"
        ),
    )

    user = db.relationship("User", back_populates="jobs")
    events = db.relationship("JobEvent", back_populates="job", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "attempts": self.attempts,
            "idempotency_key": self.idempotency_key,
            "celery_task_id": self.celery_task_id,
            "error": self.error,
            "retried_to_job_id": self.retried_to_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class JobEvent(db.Model):
    __tablename__ = "job_events"

    id: int = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    job_id: str = db.Column(
        db.String(36), db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: str = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    type: str = db.Column(db.Text, nullable=False)
    payload: dict = db.Column(db.JSON, nullable=False, default=dict)
    event_ulid: str = db.Column(db.Text, nullable=False, unique=True)
    created_at: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    job = db.relationship("Job", back_populates="events")
