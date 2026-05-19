# Flask 애플리케이션 팩토리
import time

from flask import Flask, g, request

from src.config import Config
from src.extensions import db, init_redis
from src.middleware.request_id import add_request_id_header, inject_request_id
from src.middleware.session import load_session
from src.utils.logging import configure_logging, get_logger
from src.utils.metrics import http_request_duration, http_requests_total

logger = get_logger(__name__)


def create_app(config: object | dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.from_object(Config)
    if isinstance(config, dict):
        app.config.update(config)
    elif config is not None:
        app.config.from_object(config)

    configure_logging(app.config.get("LOG_LEVEL", "INFO"))
    db.init_app(app)
    init_redis(app.config["REDIS_URL"])

    _register_hooks(app)
    _register_blueprints(app)

    return app


def _register_hooks(app: Flask) -> None:
    @app.before_request
    def before():
        inject_request_id()
        load_session()
        g._start_time = time.perf_counter()

    @app.after_request
    def after(response):
        add_request_id_header(response)
        elapsed = time.perf_counter() - getattr(g, "_start_time", time.perf_counter())
        route = request.endpoint or "unknown"
        method = request.method
        status = str(response.status_code)
        http_request_duration.labels(  # noqa: E501
            method=method, route=route, status_code=status
        ).observe(elapsed)
        http_requests_total.labels(method=method, route=route, status_code=status).inc()
        return response


def _register_blueprints(app: Flask) -> None:
    from src.blueprints.auth import bp as auth_bp
    from src.blueprints.events import bp as events_bp
    from src.blueprints.healthz import bp as healthz_bp
    from src.blueprints.jobs import bp as jobs_bp
    from src.blueprints.metrics import bp as metrics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(healthz_bp)
