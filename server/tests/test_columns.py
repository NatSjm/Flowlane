from fastapi.testclient import TestClient
from httpx2 import Response

from tests.conftest import (
    assert_error,
    board_with_columns,
    create_board,
    create_column,
    create_task,
    get_board,
)

COLUMN_KEYS = {"id", "boardId", "name", "position", "createdAt", "updatedAt"}

# ---------------------------------------------------------------------------
# POST /boards/{boardId}/columns
# ---------------------------------------------------------------------------


def test_create_column_appends_at_end(client: TestClient) -> None:
    board = create_board(client)

    response = client.post(f"/api/boards/{board['id']}/columns", json={"name": "  Review  "})

    assert response.status_code == 201
    column = response.json()
    assert set(column) == COLUMN_KEYS
    assert column["id"].startswith("column-")
    assert column["boardId"] == board["id"]
    assert column["name"] == "Review"
    assert column["position"] == 3  # after the three seeded defaults
    assert column["createdAt"] == column["updatedAt"]

    detail = get_board(client, board["id"])
    assert [c["position"] for c in detail["columns"]] == [0, 1, 2, 3]
    assert detail["columns"][3]["id"] == column["id"]
    assert detail["columns"][3]["tasks"] == []


def test_create_column_positions_are_per_board(client: TestClient) -> None:
    a = create_board(client, "a")
    b = create_board(client, "b")
    create_column(client, a["id"], "extra on a")

    assert create_column(client, b["id"], "extra on b")["position"] == 3


def test_create_column_rejects_empty_name(client: TestClient) -> None:
    board = create_board(client)
    response = client.post(f"/api/boards/{board['id']}/columns", json={"name": " "})
    assert_error(response, 400, "VALIDATION_ERROR", "Column name is required")


def test_create_column_rejects_missing_name(client: TestClient) -> None:
    board = create_board(client)
    response = client.post(f"/api/boards/{board['id']}/columns", json={})
    assert_error(response, 400, "VALIDATION_ERROR")


def test_create_column_rejects_name_over_50_chars(client: TestClient) -> None:
    board = create_board(client)
    response = client.post(f"/api/boards/{board['id']}/columns", json={"name": "x" * 51})
    assert_error(response, 400, "VALIDATION_ERROR", "Column name must be 50 characters or fewer")


def test_create_column_unknown_board_returns_404(client: TestClient) -> None:
    response = client.post("/api/boards/board-nope/columns", json={"name": "x"})
    assert_error(response, 404, "NOT_FOUND", "Board not found")


# ---------------------------------------------------------------------------
# PATCH /columns/{columnId}
# ---------------------------------------------------------------------------


def test_update_column_renames(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column = columns[0]

    response = client.patch(f"/api/columns/{column['id']}", json={"name": " Backlog "})

    assert response.status_code == 200
    updated = response.json()
    assert set(updated) == COLUMN_KEYS
    assert updated["id"] == column["id"]
    assert updated["boardId"] == board["id"]
    assert updated["name"] == "Backlog"
    assert updated["position"] == column["position"]
    assert updated["updatedAt"] >= column["updatedAt"]
    assert get_board(client, board["id"])["columns"][0]["name"] == "Backlog"


def test_update_column_rejects_empty_name(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    response = client.patch(f"/api/columns/{columns[0]['id']}", json={"name": ""})
    assert_error(response, 400, "VALIDATION_ERROR", "Column name is required")


def test_update_column_unknown_id_returns_404(client: TestClient) -> None:
    response = client.patch("/api/columns/column-nope", json={"name": "x"})
    assert_error(response, 404, "NOT_FOUND", "Column not found")


# ---------------------------------------------------------------------------
# DELETE /columns/{columnId}
# ---------------------------------------------------------------------------


def test_delete_column_reindexes_siblings(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    todo, in_progress, done = columns

    response = client.delete(f"/api/columns/{in_progress['id']}")

    assert response.status_code == 204
    assert response.content == b""
    remaining = get_board(client, board["id"])["columns"]
    assert [c["id"] for c in remaining] == [todo["id"], done["id"]]
    assert [c["position"] for c in remaining] == [0, 1]


def test_delete_column_cascades_to_tasks(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])

    client.delete(f"/api/columns/{columns[0]['id']}")

    assert_error(client.get(f"/api/tasks/{task['id']}"), 404, "NOT_FOUND", "Task not found")


def test_delete_column_leaves_board_summary_counts_consistent(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    create_task(client, columns[0]["id"])
    create_task(client, columns[1]["id"])

    client.delete(f"/api/columns/{columns[0]['id']}")

    (summary,) = client.get("/api/boards").json()
    assert summary["id"] == board["id"]
    assert summary["columnCount"] == 2
    assert summary["taskCount"] == 1


def test_delete_column_unknown_id_returns_404(client: TestClient) -> None:
    assert_error(client.delete("/api/columns/column-nope"), 404, "NOT_FOUND", "Column not found")


# ---------------------------------------------------------------------------
# PATCH /boards/{boardId}/columns/reorder
# ---------------------------------------------------------------------------


def reorder(client: TestClient, board_id: str, column_ids: list[str]) -> Response:
    return client.patch(f"/api/boards/{board_id}/columns/reorder", json={"columnIds": column_ids})


def test_reorder_columns_sets_positions_from_array_index(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    todo, in_progress, done = columns
    new_order = [done["id"], todo["id"], in_progress["id"]]

    response = reorder(client, board["id"], new_order)

    assert response.status_code == 200
    reordered = response.json()
    assert [c["id"] for c in reordered] == new_order
    assert [c["position"] for c in reordered] == [0, 1, 2]
    assert set(reordered[0]) == COLUMN_KEYS

    detail = get_board(client, board["id"])
    assert [c["id"] for c in detail["columns"]] == new_order


def test_reorder_columns_preserves_tasks(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    todo, in_progress, done = columns
    task = create_task(client, todo["id"])

    reorder(client, board["id"], [done["id"], in_progress["id"], todo["id"]])

    detail = get_board(client, board["id"])
    assert detail["columns"][2]["id"] == todo["id"]
    assert [t["id"] for t in detail["columns"][2]["tasks"]] == [task["id"]]


def test_reorder_columns_unknown_board_returns_404(client: TestClient) -> None:
    assert_error(reorder(client, "board-nope", []), 404, "NOT_FOUND", "Board not found")


def test_reorder_columns_unknown_column_returns_404(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    ids = [c["id"] for c in columns]
    ids[1] = "column-nope"

    assert_error(reorder(client, board["id"], ids), 404, "NOT_FOUND", "Column not found")
    # Nothing was applied.
    assert [c["position"] for c in get_board(client, board["id"])["columns"]] == [0, 1, 2]


def test_reorder_columns_rejects_column_from_another_board(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    _, other_columns = board_with_columns(client)
    ids = [c["id"] for c in columns]
    ids[0] = other_columns[0]["id"]

    assert_error(reorder(client, board["id"], ids), 404, "NOT_FOUND", "Column not found")


def test_reorder_columns_must_list_every_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)

    response = reorder(client, board["id"], [columns[0]["id"], columns[1]["id"]])

    assert_error(response, 400, "VALIDATION_ERROR")
    assert [c["position"] for c in get_board(client, board["id"])["columns"]] == [0, 1, 2]


def test_reorder_columns_rejects_duplicates(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    ids = [columns[0]["id"], columns[0]["id"], columns[1]["id"]]

    assert_error(reorder(client, board["id"], ids), 400, "VALIDATION_ERROR")


def test_reorder_columns_rejects_missing_column_ids(client: TestClient) -> None:
    board = create_board(client)
    response = client.patch(f"/api/boards/{board['id']}/columns/reorder", json={})
    assert_error(response, 400, "VALIDATION_ERROR")
