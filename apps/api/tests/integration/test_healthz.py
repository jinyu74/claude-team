# 헬스체크 엔드포인트 통합 테스트


class TestHealthz:
    def test_healthz_returns_ok(self, client, app):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
