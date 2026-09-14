"""The database layer itself: configuration, durability across restarts, transactions."""

from pathlib import Path
from typing import get_args

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.pool import QueuePool, StaticPool

from flowlane_api.common import utcnow
from flowlane_api.config import DEFAULT_DATABASE_URL, Settings, load_settings
from flowlane_api.db import create_db_engine, init_db
from flowlane_api.dependencies import StoreDep
from flowlane_api.errors import NotFoundError
from flowlane_api.main import create_app
from flowlane_api.models import BoardRecord
from tests.conftest import assert_error, create_board, create_column, create_task, get_board


def test_database_url_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./somewhere.sqlite3")
    assert load_settings().database_url == "sqlite:///./somewhere.sqlite3"


def test_database_url_defaults_to_a_sqlite_file_next_to_the_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)  # no .env file in reach
    assert load_settings().database_url == DEFAULT_DATABASE_URL
    assert DEFAULT_DATABASE_URL.startswith("sqlite:///")
    assert DEFAULT_DATABASE_URL.endswith("/server/flowlane.sqlite3")


def test_dotenv_file_in_the_working_directory_is_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///./from-dotenv.sqlite3\nSQL_ECHO=1\n")

    settings = load_settings()

    assert settings.database_url == "sqlite:///./from-dotenv.sqlite3"
    assert settings.sql_echo is True


def test_environment_variable_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///./from-dotenv.sqlite3\n")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./from-env.sqlite3")

    assert load_settings().database_url == "sqlite:///./from-env.sqlite3"


def test_sql_echo_defaults_off(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SQL_ECHO", raising=False)
    monkeypatch.chdir(tmp_path)
    assert load_settings().sql_echo is False


# --- engine -----------------------------------------------------------------


def test_in_memory_sqlite_shares_one_connection() -> None:
    """`sqlite://` databases live inside a connection; every session must get the same one
    or each request would see an empty database."""
    engine = create_db_engine("sqlite://")
    assert isinstance(engine.pool, StaticPool)
    engine.dispose()


def test_file_sqlite_uses_a_regular_pool(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{(tmp_path / 'pool.sqlite3').as_posix()}")
    assert isinstance(engine.pool, QueuePool)
    engine.dispose()


def test_init_db_creates_the_schema(tmp_path: Path) -> None:
    engine = create_db_engine(f"sqlite:///{(tmp_path / 'schema.sqlite3').as_posix()}")
    init_db(engine)
    assert set(inspect(engine).get_table_names()) == {"boards", "columns", "tasks"}
    engine.dispose()


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    """Every startup calls it; existing tables (and their data) must be left alone."""
    url = f"sqlite:///{(tmp_path / 'again.sqlite3').as_posix()}"
    with TestClient(create_app(Settings(database_url=url))) as client:
        create_board(client, "Kept")

    engine = create_db_engine(url)
    init_db(engine)
    init_db(engine)
    engine.dispose()

    with TestClient(create_app(Settings(database_url=url))) as client:
        assert [b["name"] for b in client.get("/api/boards").json()] == ["Kept"]


# --- durability & transactions ------------------------------------------------


def test_data_survives_an_app_restart(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'flowlane.sqlite3').as_posix()}")

    with TestClient(create_app(settings)) as client:
        board = create_board(client, "Durable")
        column_id = get_board(client, board["id"])["columns"][0]["id"]
        task = create_task(client, column_id, "Still here", priority="HIGH")

    with TestClient(create_app(settings)) as client:
        boards = client.get("/api/boards").json()
        assert [b["name"] for b in boards] == ["Durable"]
        assert boards[0]["columnCount"] == 3
        assert boards[0]["taskCount"] == 1
        detail = get_board(client, board["id"])
        (stored,) = detail["columns"][0]["tasks"]
        assert stored == task  # ids, timestamps and priority round-trip byte for byte


def test_failed_request_is_rolled_back() -> None:
    """Writes made before an endpoint raises must not be committed."""
    app = create_app(Settings(database_url="sqlite://"))

    @app.post("/boom")
    def write_then_fail(store: StoreDep) -> None:
        now = utcnow()
        store.boards.add(
            BoardRecord(
                id="board-doomed", name="Doomed", owner_id="x", created_at=now, updated_at=now
            )
        )
        raise NotFoundError("Board not found")

    with TestClient(app) as client:
        assert_error(client.post("/boom"), 404, "NOT_FOUND")
        assert client.get("/api/boards").json() == []
        # The failed session was discarded; the next request gets a clean one.
        create_board(client, "After the failure")
        assert [b["name"] for b in client.get("/api/boards").json()] == ["After the failure"]


def test_each_request_sees_the_previous_request_commit(client: TestClient) -> None:
    """One session per request: what request N committed is visible to request N+1,
    including through a different repository (task counts come from a COUNT query)."""
    board = create_board(client)
    columns = get_board(client, board["id"])["columns"]
    create_task(client, columns[0]["id"], "a")
    create_task(client, columns[1]["id"], "b")

    (summary,) = client.get("/api/boards").json()
    assert summary["taskCount"] == 2


def test_board_with_no_columns_reports_zero_tasks(client: TestClient) -> None:
    """`count_for_columns([])` must short-circuit rather than emit `IN ()`."""
    board = create_board(client)
    for column in get_board(client, board["id"])["columns"]:
        assert client.delete(f"/api/columns/{column['id']}").status_code == 204

    (summary,) = client.get("/api/boards").json()
    assert summary["columnCount"] == 0
    assert summary["taskCount"] == 0


def test_many_rows_keep_their_order_after_restart(tmp_path: Path) -> None:
    """Ordering comes from ORDER BY, not insertion or id order."""
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'order.sqlite3').as_posix()}")
    with TestClient(create_app(settings)) as client:
        board = create_board(client)
        column_ids = [c["id"] for c in get_board(client, board["id"])["columns"]]
        for extra in ("Review", "Blocked"):
            column_ids.append(create_column(client, board["id"], extra)["id"])
        titles = [f"task {i}" for i in range(12)]
        task_ids = [create_task(client, column_ids[0], t)["id"] for t in titles]
        # Reverse the columns and move the last task to the front of its column.
        reversed_ids = list(reversed(column_ids))
        response = client.patch(
            f"/api/boards/{board['id']}/columns/reorder", json={"columnIds": reversed_ids}
        )
        assert response.status_code == 200
        response = client.patch(
            f"/api/tasks/{task_ids[-1]}/move", json={"columnId": column_ids[0], "position": 0}
        )
        assert response.status_code == 200

    with TestClient(create_app(settings)) as client:
        detail = get_board(client, board["id"])
        assert [c["id"] for c in detail["columns"]] == reversed_ids
        (first_column,) = [c for c in detail["columns"] if c["id"] == column_ids[0]]
        assert [t["title"] for t in first_column["tasks"]] == [titles[-1], *titles[:-1]]
        assert [t["position"] for t in first_column["tasks"]] == list(range(12))


def test_commit_happens_before_the_response_is_sent() -> None:
    """`get_store` must be function-scoped: with FastAPI's default request scope the
    commit would run after the response, so a client's follow-up read could miss it."""
    (_, depends) = get_args(StoreDep)
    assert depends.scope == "function"
