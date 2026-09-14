"""App-level behavior not tied to a single resource."""

from fastapi.testclient import TestClient

from tests.conftest import assert_error


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    assert_error(client.get("/api/nope"), 404, "NOT_FOUND")


def test_unsupported_method_uses_error_envelope(client: TestClient) -> None:
    response = client.put("/api/boards")
    assert response.status_code == 405
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}


def test_endpoints_are_mounted_under_api_prefix(client: TestClient) -> None:
    # openapi.yaml declares `servers: [{url: /api}]`; the frontend fetches relative to it.
    assert client.get("/api/boards").status_code == 200
    assert client.get("/boards").status_code == 404


def test_openapi_schema_is_served(client: TestClient) -> None:
    schema = client.get("/api/openapi.json").json()
    assert schema["info"]["title"] == "Flowlane API"
    assert "/api/boards/{boardId}/columns/reorder" in schema["paths"]


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
