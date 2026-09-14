"""Shared fixtures: a fresh app + empty SQLite database per test."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from flowlane_api.config import Settings
from flowlane_api.main import create_app

# In-memory SQLite: created by the app's lifespan on startup, gone when the engine is
# disposed on shutdown — so `with TestClient(app)` bounds each test's database.
TEST_DATABASE_URL = "sqlite://"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(database_url=TEST_DATABASE_URL))
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Small helpers so each test reads as "arrange â†’ act â†’ assert" without
# repeating the create-board / create-column / create-task boilerplate.
# ---------------------------------------------------------------------------

Json = dict[str, Any]


def create_board(client: TestClient, name: str = "Board") -> Json:
    response = client.post("/api/boards", json={"name": name})
    assert response.status_code == 201, response.text
    board: Json = response.json()
    return board


def get_board(client: TestClient, board_id: str) -> Json:
    response = client.get(f"/api/boards/{board_id}")
    assert response.status_code == 200, response.text
    board: Json = response.json()
    return board


def create_column(client: TestClient, board_id: str, name: str = "Column") -> Json:
    response = client.post(f"/api/boards/{board_id}/columns", json={"name": name})
    assert response.status_code == 201, response.text
    column: Json = response.json()
    return column


def create_task(client: TestClient, column_id: str, title: str = "Task", **extra: Any) -> Json:
    response = client.post(f"/api/columns/{column_id}/tasks", json={"title": title, **extra})
    assert response.status_code == 201, response.text
    task: Json = response.json()
    return task


def board_with_columns(client: TestClient) -> tuple[Json, list[Json]]:
    """A fresh board plus its three seeded columns, sorted by position."""
    board = create_board(client)
    columns: list[Json] = get_board(client, board["id"])["columns"]
    return board, columns


def column_task_ids(client: TestClient, board_id: str, column_id: str) -> list[str]:
    """Task ids in `column_id` as returned by GET /boards/{id} (i.e. sorted by position).

    Also asserts the column's positions are contiguous (0, 1, 2, â€¦), which every
    task mutation is required to maintain.
    """
    board = get_board(client, board_id)
    (column,) = [c for c in board["columns"] if c["id"] == column_id]
    tasks: list[Json] = column["tasks"]
    assert [t["position"] for t in tasks] == list(range(len(tasks))), "positions not contiguous"
    return [t["id"] for t in tasks]


def assert_error(response: Response, status: int, code: str, message: str | None = None) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    if message is not None:
        assert body["error"]["message"] == message
