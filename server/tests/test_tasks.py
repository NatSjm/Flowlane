from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from tests.conftest import (
    assert_error,
    board_with_columns,
    column_task_ids,
    create_task,
)

TASK_KEYS = {
    "id",
    "columnId",
    "title",
    "description",
    "priority",
    "position",
    "dueDate",
    "createdAt",
    "updatedAt",
}

# ---------------------------------------------------------------------------
# POST /columns/{columnId}/tasks
# ---------------------------------------------------------------------------


def test_create_task_with_defaults(client: TestClient) -> None:
    _, columns = board_with_columns(client)

    response = client.post(f"/api/columns/{columns[0]['id']}/tasks", json={"title": "Write tests"})

    assert response.status_code == 201
    task = response.json()
    assert set(task) == TASK_KEYS
    assert task["id"].startswith("task-")
    assert task["columnId"] == columns[0]["id"]
    assert task["title"] == "Write tests"
    assert task["description"] == ""
    assert task["priority"] == "MEDIUM"
    assert task["position"] == 0
    assert task["dueDate"] is None
    datetime.fromisoformat(task["createdAt"])
    assert task["createdAt"] == task["updatedAt"]


def test_create_task_with_all_fields(client: TestClient) -> None:
    _, columns = board_with_columns(client)

    task = create_task(
        client,
        columns[0]["id"],
        "  Ship it  ",
        description="  Details here  ",
        priority="HIGH",
        dueDate="2026-10-01T12:00:00Z",
    )

    assert task["title"] == "Ship it"
    assert task["description"] == "Details here"
    assert task["priority"] == "HIGH"
    assert datetime.fromisoformat(task["dueDate"]) == datetime.fromisoformat("2026-10-01T12:00:00Z")


def test_create_task_accepts_explicit_null_due_date(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    assert create_task(client, columns[0]["id"], dueDate=None)["dueDate"] is None


def test_create_task_appends_at_end_of_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]

    first = create_task(client, column_id, "first")
    second = create_task(client, column_id, "second")
    # A task in a different column doesn't affect this column's positions.
    other = create_task(client, columns[1]["id"], "other")
    third = create_task(client, column_id, "third")

    assert [first["position"], second["position"], third["position"]] == [0, 1, 2]
    assert other["position"] == 0
    assert column_task_ids(client, board["id"], column_id) == [
        first["id"],
        second["id"],
        third["id"],
    ]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"title": ""}, "Task title is required"),
        ({"title": "   "}, "Task title is required"),
        ({"title": "x" * 201}, "Title must be 200 characters or fewer"),
        (
            {"title": "ok", "description": "x" * 5001},
            "Description must be 5000 characters or fewer",
        ),
        ({"title": "ok", "dueDate": "not-a-date"}, "Due date must be a valid date"),
    ],
)
def test_create_task_validation_messages(
    client: TestClient, body: dict[str, str], message: str
) -> None:
    _, columns = board_with_columns(client)
    response = client.post(f"/api/columns/{columns[0]['id']}/tasks", json=body)
    assert_error(response, 400, "VALIDATION_ERROR", message)


@pytest.mark.parametrize(
    "body",
    [
        {},  # title missing
        {"title": "ok", "priority": "URGENT"},  # not in the enum
        {"title": "ok", "priority": "high"},  # enum is case-sensitive
        {"title": "ok", "description": None},  # description is not nullable
        {"title": 123},
    ],
)
def test_create_task_rejects_invalid_bodies(client: TestClient, body: dict[str, object]) -> None:
    _, columns = board_with_columns(client)
    response = client.post(f"/api/columns/{columns[0]['id']}/tasks", json=body)
    assert_error(response, 400, "VALIDATION_ERROR")


def test_create_task_accepts_boundary_lengths(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], "t" * 200, description="d" * 5000)
    assert len(task["title"]) == 200
    assert len(task["description"]) == 5000


def test_create_task_unknown_column_returns_404(client: TestClient) -> None:
    response = client.post("/api/columns/column-nope/tasks", json={"title": "x"})
    assert_error(response, 404, "NOT_FOUND", "Column not found")


# ---------------------------------------------------------------------------
# GET /tasks/{taskId}
# ---------------------------------------------------------------------------


def test_get_task(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    created = create_task(client, columns[0]["id"], "Read me", priority="LOW")

    response = client.get(f"/api/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_task_unknown_id_returns_404(client: TestClient) -> None:
    assert_error(client.get("/api/tasks/task-nope"), 404, "NOT_FOUND", "Task not found")


# ---------------------------------------------------------------------------
# PATCH /tasks/{taskId}
# ---------------------------------------------------------------------------


def test_update_task_partial_only_changes_supplied_fields(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], "Original", description="keep me", priority="HIGH")

    response = client.patch(f"/api/tasks/{task['id']}", json={"title": "  Renamed  "})

    assert response.status_code == 200
    updated = response.json()
    assert set(updated) == TASK_KEYS
    assert updated["id"] == task["id"]
    assert updated["title"] == "Renamed"
    assert updated["description"] == "keep me"
    assert updated["priority"] == "HIGH"
    assert updated["columnId"] == task["columnId"]
    assert updated["position"] == task["position"]
    assert updated["createdAt"] == task["createdAt"]
    assert updated["updatedAt"] >= task["updatedAt"]
    assert client.get(f"/api/tasks/{task['id']}").json() == updated


def test_update_task_all_fields(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])

    response = client.patch(
        f"/api/tasks/{task['id']}",
        json={
            "title": "New title",
            "description": "  New description  ",
            "priority": "LOW",
            "dueDate": "2026-12-24T09:30:00Z",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "New title"
    assert updated["description"] == "New description"
    assert updated["priority"] == "LOW"
    assert datetime.fromisoformat(updated["dueDate"]) == datetime.fromisoformat(
        "2026-12-24T09:30:00Z"
    )


def test_update_task_can_clear_due_date_with_null(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], dueDate="2026-10-01T00:00:00Z")
    assert task["dueDate"] is not None

    response = client.patch(f"/api/tasks/{task['id']}", json={"dueDate": None})

    assert response.status_code == 200
    assert response.json()["dueDate"] is None


def test_update_task_omitting_due_date_keeps_it(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], dueDate="2026-10-01T00:00:00Z")

    response = client.patch(f"/api/tasks/{task['id']}", json={"title": "x"})

    assert response.json()["dueDate"] == task["dueDate"]


def test_update_task_empty_body_is_a_noop(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], "Same")

    response = client.patch(f"/api/tasks/{task['id']}", json={})

    assert response.status_code == 200
    body = response.json()
    assert {k: v for k, v in body.items() if k != "updatedAt"} == {
        k: v for k, v in task.items() if k != "updatedAt"
    }


def test_update_task_ignores_read_only_fields(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    create_task(client, columns[0]["id"], "first")
    task = create_task(client, columns[0]["id"], "second")

    response = client.patch(
        f"/api/tasks/{task['id']}", json={"position": 0, "id": "task-hijack", "title": "ok"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == task["id"]
    assert response.json()["position"] == 1


def test_update_task_with_column_id_moves_to_end_of_target(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    source, target = columns[0]["id"], columns[1]["id"]
    a = create_task(client, source, "a")
    b = create_task(client, source, "b")
    c = create_task(client, source, "c")
    existing = create_task(client, target, "existing")

    response = client.patch(f"/api/tasks/{b['id']}", json={"columnId": target})

    assert response.status_code == 200
    moved = response.json()
    assert moved["columnId"] == target
    assert moved["position"] == 1
    assert column_task_ids(client, board["id"], source) == [a["id"], c["id"]]
    assert column_task_ids(client, board["id"], target) == [existing["id"], b["id"]]


def test_update_task_with_same_column_id_keeps_position(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")

    response = client.patch(f"/api/tasks/{a['id']}", json={"columnId": column_id})

    assert response.status_code == 200
    assert response.json()["position"] == 0
    assert column_task_ids(client, board["id"], column_id) == [a["id"], b["id"]]


def test_update_task_can_move_and_edit_at_once(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], "a")

    response = client.patch(
        f"/api/tasks/{task['id']}", json={"columnId": columns[2]["id"], "title": "done!"}
    )

    assert response.status_code == 200
    assert response.json()["columnId"] == columns[2]["id"]
    assert response.json()["title"] == "done!"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"title": ""}, "Task title is required"),
        ({"title": "x" * 201}, "Title must be 200 characters or fewer"),
        ({"description": "x" * 5001}, "Description must be 5000 characters or fewer"),
        ({"dueDate": "yesterday-ish"}, "Due date must be a valid date"),
    ],
)
def test_update_task_validation_messages(
    client: TestClient, body: dict[str, str], message: str
) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])
    response = client.patch(f"/api/tasks/{task['id']}", json=body)
    assert_error(response, 400, "VALIDATION_ERROR", message)


@pytest.mark.parametrize(
    "body",
    [
        {"priority": "CRITICAL"},
        {"title": None},
        {"description": None},
        {"columnId": None},
    ],
)
def test_update_task_rejects_invalid_bodies(client: TestClient, body: dict[str, object]) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])
    response = client.patch(f"/api/tasks/{task['id']}", json=body)
    assert_error(response, 400, "VALIDATION_ERROR")


def test_update_task_unknown_task_returns_404(client: TestClient) -> None:
    response = client.patch("/api/tasks/task-nope", json={"title": "x"})
    assert_error(response, 404, "NOT_FOUND", "Task not found")


def test_update_task_unknown_target_column_returns_404(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"], "stay")

    response = client.patch(f"/api/tasks/{task['id']}", json={"columnId": "column-nope"})

    assert_error(response, 404, "NOT_FOUND", "Column not found")
    assert client.get(f"/api/tasks/{task['id']}").json()["columnId"] == columns[0]["id"]


# ---------------------------------------------------------------------------
# DELETE /tasks/{taskId}
# ---------------------------------------------------------------------------


def test_delete_task_reindexes_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")
    c = create_task(client, column_id, "c")

    response = client.delete(f"/api/tasks/{b['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/tasks/{b['id']}").status_code == 404
    assert column_task_ids(client, board["id"], column_id) == [a["id"], c["id"]]


def test_delete_task_unknown_id_returns_404(client: TestClient) -> None:
    assert_error(client.delete("/api/tasks/task-nope"), 404, "NOT_FOUND", "Task not found")


# ---------------------------------------------------------------------------
# PATCH /tasks/{taskId}/move
# ---------------------------------------------------------------------------


def move(client: TestClient, task_id: str, column_id: str, position: int) -> Response:
    return client.patch(
        f"/api/tasks/{task_id}/move", json={"columnId": column_id, "position": position}
    )


def test_move_task_reorders_within_same_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")
    c = create_task(client, column_id, "c")

    response = move(client, c["id"], column_id, 0)

    assert response.status_code == 200
    moved = response.json()
    assert set(moved) == TASK_KEYS
    assert moved["id"] == c["id"]
    assert moved["columnId"] == column_id
    assert moved["position"] == 0
    assert moved["updatedAt"] >= c["updatedAt"]
    assert column_task_ids(client, board["id"], column_id) == [c["id"], a["id"], b["id"]]


def test_move_task_down_within_same_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")
    c = create_task(client, column_id, "c")

    response = move(client, a["id"], column_id, 2)

    assert response.json()["position"] == 2
    assert column_task_ids(client, board["id"], column_id) == [b["id"], c["id"], a["id"]]


def test_move_task_to_same_position_is_a_noop(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")

    response = move(client, b["id"], column_id, 1)

    assert response.status_code == 200
    assert response.json()["position"] == 1
    assert column_task_ids(client, board["id"], column_id) == [a["id"], b["id"]]


def test_move_task_to_another_column_at_index(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    source, target = columns[0]["id"], columns[1]["id"]
    s1 = create_task(client, source, "s1")
    s2 = create_task(client, source, "s2")
    s3 = create_task(client, source, "s3")
    t1 = create_task(client, target, "t1")
    t2 = create_task(client, target, "t2")

    response = move(client, s2["id"], target, 1)

    assert response.status_code == 200
    assert response.json()["columnId"] == target
    assert response.json()["position"] == 1
    # Source is reindexed (the gap where s2 was is closed)…
    assert column_task_ids(client, board["id"], source) == [s1["id"], s3["id"]]
    # …and the destination has s2 spliced in at index 1.
    assert column_task_ids(client, board["id"], target) == [t1["id"], s2["id"], t2["id"]]


def test_move_task_to_empty_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    source, target = columns[0]["id"], columns[2]["id"]
    task = create_task(client, source)

    response = move(client, task["id"], target, 0)

    assert response.json()["position"] == 0
    assert column_task_ids(client, board["id"], source) == []
    assert column_task_ids(client, board["id"], target) == [task["id"]]


def test_move_task_clamps_position_beyond_end(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    source, target = columns[0]["id"], columns[1]["id"]
    task = create_task(client, source)
    t1 = create_task(client, target, "t1")

    response = move(client, task["id"], target, 999)

    assert response.status_code == 200
    assert response.json()["position"] == 1
    assert column_task_ids(client, board["id"], target) == [t1["id"], task["id"]]


def test_move_task_clamps_position_within_same_column(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")

    response = move(client, a["id"], column_id, 50)

    # Same-column moves clamp to the post-move order, so the max index is len - 1.
    assert response.json()["position"] == 1
    assert column_task_ids(client, board["id"], column_id) == [b["id"], a["id"]]


def test_move_task_rejects_negative_position(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])
    assert_error(move(client, task["id"], columns[0]["id"], -1), 400, "VALIDATION_ERROR")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"columnId": "will-be-filled"},  # position missing
        {"position": 0},  # columnId missing
        {"columnId": "will-be-filled", "position": "first"},
        {"columnId": "will-be-filled", "position": 1.5},
    ],
)
def test_move_task_rejects_invalid_bodies(client: TestClient, body: dict[str, object]) -> None:
    _, columns = board_with_columns(client)
    task = create_task(client, columns[0]["id"])
    if body.get("columnId") == "will-be-filled":
        body["columnId"] = columns[0]["id"]

    response = client.patch(f"/api/tasks/{task['id']}/move", json=body)

    assert_error(response, 400, "VALIDATION_ERROR")


def test_move_task_unknown_task_returns_404(client: TestClient) -> None:
    _, columns = board_with_columns(client)
    assert_error(move(client, "task-nope", columns[0]["id"], 0), 404, "NOT_FOUND", "Task not found")


def test_move_task_unknown_column_returns_404_and_changes_nothing(client: TestClient) -> None:
    board, columns = board_with_columns(client)
    column_id = columns[0]["id"]
    a = create_task(client, column_id, "a")
    b = create_task(client, column_id, "b")

    assert_error(move(client, a["id"], "column-nope", 0), 404, "NOT_FOUND", "Column not found")
    assert column_task_ids(client, board["id"], column_id) == [a["id"], b["id"]]


def test_move_task_reflected_in_board_detail_nesting(client: TestClient) -> None:
    """End-to-end: the drag-and-drop payload the board page reads stays consistent."""
    board, columns = board_with_columns(client)
    todo, in_progress, done = (c["id"] for c in columns)
    x = create_task(client, todo, "x")
    y = create_task(client, todo, "y")
    z = create_task(client, in_progress, "z")

    move(client, x["id"], in_progress, 0)
    move(client, z["id"], done, 0)
    move(client, y["id"], in_progress, 1)

    detail = client.get(f"/api/boards/{board['id']}").json()
    by_column = {c["id"]: [t["id"] for t in c["tasks"]] for c in detail["columns"]}
    assert by_column == {todo: [], in_progress: [x["id"], y["id"]], done: [z["id"]]}
    for column in detail["columns"]:
        assert [t["position"] for t in column["tasks"]] == list(range(len(column["tasks"])))
        assert all(t["columnId"] == column["id"] for t in column["tasks"])
