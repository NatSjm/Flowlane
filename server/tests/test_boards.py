from datetime import datetime

from fastapi.testclient import TestClient

from tests.conftest import (
    assert_error,
    board_with_columns,
    create_board,
    create_column,
    create_task,
    get_board,
)

BOARD_KEYS = {"id", "name", "ownerId", "createdAt", "updatedAt"}

# ---------------------------------------------------------------------------
# POST /boards
# ---------------------------------------------------------------------------


def test_create_board_returns_201_with_board_shape(client: TestClient) -> None:
    response = client.post("/api/boards", json={"name": "Website Redesign"})

    assert response.status_code == 201
    board = response.json()
    assert set(board) == BOARD_KEYS
    assert board["id"].startswith("board-")
    assert board["name"] == "Website Redesign"
    assert board["ownerId"] == "local-user"
    # ISO-8601 timestamps the frontend can parse with `new Date(...)`.
    datetime.fromisoformat(board["createdAt"])
    assert board["createdAt"] == board["updatedAt"]


def test_create_board_trims_name(client: TestClient) -> None:
    assert create_board(client, "  Padded  ")["name"] == "Padded"


def test_create_board_seeds_default_columns(client: TestClient) -> None:
    board = create_board(client)

    detail = get_board(client, board["id"])
    assert [c["name"] for c in detail["columns"]] == ["Todo", "In Progress", "Done"]
    assert [c["position"] for c in detail["columns"]] == [0, 1, 2]
    assert all(c["boardId"] == board["id"] for c in detail["columns"])
    assert all(c["tasks"] == [] for c in detail["columns"])


def test_create_board_generates_unique_ids(client: TestClient) -> None:
    assert create_board(client)["id"] != create_board(client)["id"]


def test_create_board_rejects_empty_name(client: TestClient) -> None:
    response = client.post("/api/boards", json={"name": "   "})
    assert_error(response, 400, "VALIDATION_ERROR", "Board name is required")


def test_create_board_rejects_missing_name(client: TestClient) -> None:
    response = client.post("/api/boards", json={})
    assert_error(response, 400, "VALIDATION_ERROR")


def test_create_board_rejects_non_string_name(client: TestClient) -> None:
    response = client.post("/api/boards", json={"name": 42})
    assert_error(response, 400, "VALIDATION_ERROR")


def test_create_board_rejects_name_over_100_chars(client: TestClient) -> None:
    response = client.post("/api/boards", json={"name": "x" * 101})
    assert_error(response, 400, "VALIDATION_ERROR", "Board name must be 100 characters or fewer")


def test_create_board_accepts_name_of_exactly_100_chars(client: TestClient) -> None:
    assert create_board(client, "x" * 100)["name"] == "x" * 100


def test_create_board_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/api/boards", content=b"not json", headers={"Content-Type": "application/json"}
    )
    assert_error(response, 400, "VALIDATION_ERROR")


# ---------------------------------------------------------------------------
# GET /boards
# ---------------------------------------------------------------------------


def test_list_boards_empty(client: TestClient) -> None:
    response = client.get("/api/boards")
    assert response.status_code == 200
    assert response.json() == []


def test_list_boards_returns_summaries_with_counts(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    create_column(client, board["id"], "Extra")
    create_task(client, columns[0]["id"], "a")
    create_task(client, columns[0]["id"], "b")
    create_task(client, columns[2]["id"], "c")

    response = client.get("/api/boards")

    assert response.status_code == 200
    (summary,) = response.json()
    assert set(summary) == BOARD_KEYS | {"columnCount", "taskCount"}
    assert summary["id"] == board["id"]
    assert summary["columnCount"] == 4
    assert summary["taskCount"] == 3


def test_list_boards_sorted_oldest_first(client: TestClient) -> None:
    first = create_board(client, "first")
    second = create_board(client, "second")
    third = create_board(client, "third")

    ids = [b["id"] for b in client.get("/api/boards").json()]
    assert ids == [first["id"], second["id"], third["id"]]


# ---------------------------------------------------------------------------
# GET /boards/{boardId}
# ---------------------------------------------------------------------------


def test_get_board_returns_nested_columns_and_tasks_sorted_by_position(
    client: TestClient,
) -> None:
    board, columns = board_with_columns(client)
    t1 = create_task(client, columns[1]["id"], "one")
    t2 = create_task(client, columns[1]["id"], "two")

    detail = get_board(client, board["id"])

    assert set(detail) == BOARD_KEYS | {"columns"}
    assert detail["id"] == board["id"]
    column = detail["columns"][1]
    assert set(column) == {"id", "boardId", "name", "position", "createdAt", "updatedAt", "tasks"}
    assert [t["id"] for t in column["tasks"]] == [t1["id"], t2["id"]]
    assert [t["position"] for t in column["tasks"]] == [0, 1]


def test_get_board_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get("/api/boards/board-does-not-exist")
    assert_error(response, 404, "NOT_FOUND", "Board not found")


# ---------------------------------------------------------------------------
# PATCH /boards/{boardId}
# ---------------------------------------------------------------------------


def test_update_board_renames(client: TestClient) -> None:
    board = create_board(client, "Old")

    response = client.patch(f"/api/boards/{board['id']}", json={"name": "  New  "})

    assert response.status_code == 200
    updated = response.json()
    assert set(updated) == BOARD_KEYS
    assert updated["id"] == board["id"]
    assert updated["name"] == "New"
    assert updated["createdAt"] == board["createdAt"]
    assert updated["updatedAt"] >= board["updatedAt"]
    assert get_board(client, board["id"])["name"] == "New"


def test_update_board_rejects_empty_name(client: TestClient) -> None:
    board = create_board(client)
    response = client.patch(f"/api/boards/{board['id']}", json={"name": ""})
    assert_error(response, 400, "VALIDATION_ERROR", "Board name is required")


def test_update_board_rejects_missing_name(client: TestClient) -> None:
    board = create_board(client)
    response = client.patch(f"/api/boards/{board['id']}", json={})
    assert_error(response, 400, "VALIDATION_ERROR")


def test_update_board_unknown_id_returns_404(client: TestClient) -> None:
    response = client.patch("/api/boards/board-nope", json={"name": "x"})
    assert_error(response, 404, "NOT_FOUND", "Board not found")


# ---------------------------------------------------------------------------
# DELETE /boards/{boardId}
# ---------------------------------------------------------------------------


def test_delete_board_returns_204_and_removes_it(client: TestClient) -> None:
    board = create_board(client)

    response = client.delete(f"/api/boards/{board['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/boards/{board['id']}").status_code == 404
    assert client.get("/api/boards").json() == []


def test_delete_board_cascades_to_columns_and_tasks(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])

    client.delete(f"/api/boards/{board['id']}")

    assert_error(client.get(f"/api/tasks/{task['id']}"), 404, "NOT_FOUND", "Task not found")
    assert_error(
        client.patch(f"/api/columns/{columns[0]['id']}", json={"name": "x"}),
        404,
        "NOT_FOUND",
        "Column not found",
    )


def test_delete_board_does_not_touch_other_boards(client: TestClient) -> None:
    doomed = create_board(client, "doomed")
    survivor, survivor_columns = board_with_columns(client)
    task = create_task(client, survivor_columns[0]["id"])

    client.delete(f"/api/boards/{doomed['id']}")

    assert len(get_board(client, survivor["id"])["columns"]) == 3
    assert client.get(f"/api/tasks/{task['id']}").status_code == 200


def test_delete_board_unknown_id_returns_404(client: TestClient) -> None:
    assert_error(client.delete("/api/boards/board-nope"), 404, "NOT_FOUND", "Board not found")
