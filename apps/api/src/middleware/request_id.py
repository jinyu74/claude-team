# X-Request-Id 요청 ID 미들웨어
import uuid
from flask import g, request, Response


def inject_request_id() -> None:
    g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())


def add_request_id_header(response: Response) -> Response:
    response.headers["X-Request-Id"] = getattr(g, "request_id", "")
    return response
