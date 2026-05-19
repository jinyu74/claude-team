"""초기 스키마 — users / jobs / job_events 테이블

Revision ID: 001
Revises:
Create Date: 2026-05-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("priority", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("celery_task_id", sa.Text, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("retried_to_job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_jobs_user_idem"),
        sa.CheckConstraint(
            "status IN ('pending','running','succeeded','failed','canceled')",
            name="ck_jobs_status",
        ),
    )
    op.create_index("ix_jobs_user_id_status", "jobs", ["user_id", "status"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "job_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            sa.String(36),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("event_ulid", sa.Text, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])
    op.create_index("ix_job_events_user_id", "job_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("job_events")
    op.drop_table("jobs")
    op.drop_table("users")
