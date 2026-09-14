# Flowlane API (backend)

FastAPI implementation of [`../openapi.yaml`](../openapi.yaml) — every endpoint, schema,
validation rule, and error shape the frontend expects. Managed with
[uv](https://docs.astral.sh/uv/); Python 3.12+.

**Persistence is SQLAlchemy** behind a small repository interface. The database is
chosen by the `DATABASE_URL` environment variable and defaults to a SQLite file
(`server/flowlane.sqlite3`, git-ignored); nothing in the code is SQLite-specific, so
PostgreSQL is a URL change plus a driver (see "Database").

## Commands

Run everything through `uv` from this directory (`server/`). `uv run` creates the
`.venv` and installs dependencies on first use, so a separate `uv sync` is optional.

```bash
uv run fastapi dev src/flowlane_api/main.py # dev server with reload → http://localhost:8000
uv run fastapi run src/flowlane_api/main.py # no reload (closer to production)
uv run pytest                               # tests
uv run ruff check .                         # lint
uv run ruff format --check .                # formatting
uv run mypy src tests                       # strict type-check
```

From the repo root, prefix with `uv --directory server …` instead of `cd`-ing. On
Windows PowerShell 5.1, chain commands with `;` — `&&` is not supported there.

### Configuration

Settings are read from environment variables, or from a `.env` file in the working
directory (`server/.env`, git-ignored — copy [`.env.example`](.env.example) to start):

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///<repo>/server/flowlane.sqlite3` | Any [SQLAlchemy URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls). `sqlite://` is an in-memory database (what the tests use). |
| `SQL_ECHO` | `0` | `1` logs every SQL statement. |

Tables are created on startup if they don't exist (`db.init_db`); there are no
migrations yet, so a schema change currently means deleting the SQLite file.

### URLs

All endpoints are mounted under `/api`, matching `servers: [{url: /api}]` in the
contract. That means the `/docs` URL printed by `fastapi dev`'s startup banner **does
not exist** (it 404s) — use these instead:

| What | URL |
| --- | --- |
| Swagger UI | http://localhost:8000/api/docs |
| Raw OpenAPI schema (generated from the app) | http://localhost:8000/api/openapi.json |
| Health check | http://localhost:8000/api/health → `{"status":"ok"}` |
| API base | http://localhost:8000/api (e.g. `GET /api/boards`) |

CORS allows the Vite dev origin (`http://localhost:5173`).

Data persists across restarts (including `fastapi dev`'s auto-reload) in the SQLite
file. Delete it for a clean slate.

## Layout

```text
src/flowlane_api/
├── main.py            # create_app(): FastAPI app, /api prefix, CORS, error handlers, DB lifespan
├── config.py          # Settings — DATABASE_URL, SQL_ECHO (env vars / .env)
├── db.py              # engine + session factory from a URL, init_db(); SQLite-only tweaks live here
├── dependencies.py    # get_store() — one session per request, commit/rollback — and service factories
├── errors.py          # NotFoundError / ValidationError + handlers → { error: { code, message } }
├── common.py          # new_id("board"|"column"|"task"), utcnow()
├── routers/           # HTTP only: boards.py, columns.py, tasks.py (one per openapi.yaml tag)
├── services/          # business rules: positions, cascades, reorder/move semantics
├── models/            # SQLAlchemy ORM (mapped dataclasses): BoardRecord, ColumnRecord, TaskRecord
├── repositories/
│   ├── protocols.py   # Store / BoardRepository / ColumnRepository / TaskRepository (Protocols)
│   └── sql.py         # SqlStore — the Store protocol on a SQLAlchemy session
└── schemas/           # Pydantic models: camelCase on the wire, snake_case in Python
tests/                 # pytest; one fresh in-memory SQLite database per test
```

Request flow: router parses the body into a `schemas` model (shape validation, trimming,
the frontend's exact error messages) → service applies the rule (existence checks,
position bookkeeping, cascades) against the `Store` → router serializes the response
model.

## Behavior worth knowing

- **Validation errors are 400**, not FastAPI's default 422, and use the envelope
  `{ "error": { "code": "VALIDATION_ERROR", "message": "…" } }`. Messages for the
  rules in `frontend/src/utils/validation.ts` are reproduced word for word
  ("Task title is required", "Board name must be 100 characters or fewer", …).
- **Names/titles/descriptions are trimmed** before validation and storage, like the
  frontend mock did.
- **`position` is server-managed**: create appends, delete reindexes, `reorder`/`move`
  set positions from the request; positions are always contiguous from 0.
- `PATCH /boards/{id}/columns/reorder` requires `columnIds` to list every column on the
  board exactly once — unknown/foreign ids are 404, missing ids or duplicates are 400,
  and nothing is applied on failure.
- `PATCH /tasks/{id}` distinguishes an omitted `dueDate` (unchanged) from `null` (cleared).
  `title`, `description`, `priority`, `columnId` may be omitted but not null.
- Timestamps are serialized like JS `Date#toISOString()` (`2026-09-14T17:54:17.343Z`).
- Unknown routes and unsupported methods also return the error envelope
  (`NOT_FOUND` / `METHOD_NOT_ALLOWED`); unhandled exceptions return `INTERNAL_ERROR`.

## Database

- **One session per request.** `dependencies.get_store` opens a SQLAlchemy session,
  hands the services a `SqlStore` over it, commits when the endpoint returns and rolls
  back when it raises. It's a function-scoped dependency so the commit lands *before*
  the response is sent.
- **Records are live ORM rows.** The repositories return session-attached instances;
  a service mutating one in place and then querying again sees its own change
  (autoflush). `add`/`save`/`delete` flush immediately so constraint errors surface at
  the call that caused them.
- **Portable schema.** Tables follow `_docs/specs.md` §5 (`boards`, `columns`,
  `tasks`). Timestamps are stored as naive UTC via `models.base.UtcDateTime` and come
  back tz-aware; `priority` is a plain VARCHAR (non-native enum); foreign keys carry
  `ON DELETE CASCADE` as a safety net behind the services' explicit cascades. Every
  constraint has a deterministic name (`models.base.NAMING_CONVENTION`) so future
  Alembic migrations can refer to them on any backend.
- **The only dialect-specific code** is `db._sqlite_engine_kwargs` /
  `_enable_sqlite_foreign_keys` — SQLite needs `check_same_thread=False` for FastAPI's
  worker threads, a shared connection for `sqlite://` in-memory databases, and
  `PRAGMA foreign_keys=ON` per connection.

### Adding PostgreSQL later

1. `uv add "psycopg[binary]"` (or another driver).
2. Set `DATABASE_URL=postgresql+psycopg://user:pass@host/flowlane`.
3. Add Alembic and generate the initial migration from `models.Base.metadata`; switch
   `db.init_db` from `create_all` to running migrations.

Nothing in `models/`, `repositories/sql.py`, the services, or the routers should need
to change.
