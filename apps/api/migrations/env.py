# Alembic 마이그레이션 환경 — Flask-SQLAlchemy 모델 자동 감지
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델 메타데이터 임포트
from src.models.user import User  # noqa: F401
from src.models.job import Job, JobEvent  # noqa: F401
from src.extensions import db
target_metadata = db.metadata


def get_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/taskqueue",
    )


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
