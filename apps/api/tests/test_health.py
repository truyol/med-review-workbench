import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.observability.request_id import REQUEST_ID_HEADER


def test_health_returns_ok_with_request_id() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]
    body = response.json()
    assert body["data"] == {"status": "ok", "service": "medreview-api"}
    assert body["meta"]["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_health_preserves_incoming_request_id() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "test-request-id"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "test-request-id"
    assert response.json()["meta"]["request_id"] == "test-request-id"


def test_ready_returns_dependency_statuses() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]
    dependencies = response.json()["data"]["dependencies"]
    assert dependencies == {"database": "ok", "storage": "ok"}


def test_unknown_route_uses_request_id_header() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers[REQUEST_ID_HEADER]
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "请求的资源不存在。",
        "next_action": "请检查地址或返回上一页。",
        "request_id": response.headers[REQUEST_ID_HEADER],
    }


def test_unhandled_error_uses_stable_error_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app: FastAPI = create_app()

    @app.get("/api/v1/_test/unhandled")
    async def raise_unhandled_error() -> None:
        raise RuntimeError("must not be exposed")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/_test/unhandled")

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER]
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert "must not be exposed" not in response.text

    log_events = [
        json.loads(line)
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("{")
    ]
    access_event = next(
        event
        for event in log_events
        if event.get("event") == "request.completed" and event.get("status") == 500
    )
    assert access_event["method"] == "GET"
    assert access_event["path"] == "/api/v1/_test/unhandled"
    assert access_event["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert isinstance(access_event["duration_ms"], int | float)


def test_cors_allows_configured_frontend_origin() -> None:
    client = TestClient(create_app())
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-expose-headers"] == "X-Request-ID"
