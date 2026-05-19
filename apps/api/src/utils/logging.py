# 구조화 JSON 로그 설정 — ADR §7.1 필수 필드
import logging

import structlog
from flask import g, has_request_context, request


def add_request_context(logger, method, event_dict):
    """요청 컨텍스트 필드 자동 삽입."""
    if has_request_context():
        event_dict.setdefault("request_id", getattr(g, "request_id", None))
        event_dict.setdefault("trace_id", getattr(g, "request_id", None))
        event_dict.setdefault("user_id", getattr(g, "current_user_id", None))
        event_dict.setdefault("route", request.endpoint)
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", key="ts"),
            add_request_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=getattr(logging, level))


def get_logger(name: str = "taskqueue"):
    return structlog.get_logger(name)
