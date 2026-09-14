# Flowlane API (backend)

FastAPI implementation of [`../openapi.yaml`](../openapi.yaml) — every endpoint, schema,
validation rule, and error shape the frontend expects. Managed with
[uv](https://docs.astral.sh/uv/); Python 3.12+.

**Persistence is a mock:** an in-memory store that lives for the life of the process and
is lost on restart. It sits behind a small repository interface so PostgreSQL can be
swapped in later without touching the routers or services (see "Replacing the mock
database").

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

The in-memory store is wiped on every restart, including the automatic reload
`fastapi dev` performs when a file under `server/` changes.

## Layout

```text
src/flowlane_api/
├── main.py            # create_app(): FastAPI app, /api prefix, CORS, error handlers
├── dependencies.py    # get_store() — the single persistence seam — and service factories
├── errors.py          # NotFoundError / ValidationError + handlers → { error: { code, message } }
├── common.py          # new_id("board"|"column"|"task"), utcnow()
├── routers/           # HTTP only: boards.py, columns.py, tasks.py (one per openapi.yaml tag)
├── services/          # business rules: positions, cascades, reorder/move semantics
├── repositories/
│   ├── protocols.py   # Store / BoardRepository / ColumnRepository / TaskRepository (Protocols)
│   ├── records.py     # plain dataclasses the repositories store and return
│   └── memory.py      # InMemoryStore — the mock database
└── schemas/           # Pydantic models: camelCase on the wire, snake_case in Python
tests/                 # pytest; one fresh InMemoryStore per test via dependency override
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

## Replacing the mock database

1. Implement the `Store` protocol in `repositories/protocols.py` on top of
   SQLAlchemy/SQLModel (one class per repository; `save()` is where a DB-backed
   implementation flushes an in-place mutation — the in-memory version's `save()` is a
   no-op).
2. Map ORM rows to/from the dataclasses in `repositories/records.py` (or make the ORM
   models satisfy the same attribute names).
3. Provide it from `dependencies.get_store` (e.g. a request-scoped session) instead of
   `app.state.store`.

The services and routers don't change; the test suite is the acceptance criterion.
