# Flowlane

A web-based Kanban board for managing tasks across the stages of a workflow: create boards, organize work into columns, and drag and drop tasks between them.

Full specification: [_docs/specs.md](_docs/specs.md) · Backend API contract: [openapi.yaml](openapi.yaml)

**Status:** the frontend is built and talks to the real backend (`server/`), which implements `openapi.yaml` on top of a SQLite database (SQLAlchemy; any backend via `DATABASE_URL`). Migrations and PostgreSQL are next.

## Features (MVP)

- Create, view, rename, and delete boards
- Default columns (Todo / In Progress / Done) plus custom columns — create, rename, delete, reorder
- Create, edit, delete, and view tasks with priority, due date, and description
- Drag and drop to reorder tasks within a column and move tasks between columns
- Search and filter tasks
- State persists across page refreshes and backend restarts (SQLite database)

See [_docs/specs.md](_docs/specs.md) for stretch features (auth, collaboration, labels, comments, etc.) and the full data model, API, and phased build plan.

## Tech Stack

| Layer | Choice |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS, `@dnd-kit` |
| API contract & codegen | [openapi.yaml](openapi.yaml), consumed by [Orval](https://orval.dev) to generate frontend types + a typed `fetch` client |
| Backend | Python, FastAPI, Pydantic, managed with [uv](https://docs.astral.sh/uv/) — implements `openapi.yaml` (see [server/README.md](server/README.md)) |
| Database | SQLAlchemy 2 — SQLite by default, any backend via `DATABASE_URL` (PostgreSQL + Alembic migrations planned) |
| Testing | Vitest, React Testing Library, Playwright (frontend, not yet written); pytest (backend) |

## How the pieces connect

[openapi.yaml](openapi.yaml) is the contract. The backend implements it under `/api`;
[Orval](https://orval.dev) generates typed `fetch` functions and model types from it
into `frontend/src/api/generated/`, which
[`frontend/src/api/client.ts`](frontend/src/api/client.ts) wraps into the `api` object
the rest of the frontend uses. In development the Vite dev server proxies `/api` to the
backend on port 8000 (`frontend/vite.config.ts`); in production the API is expected to
be served same-origin. See [frontend/README.md](frontend/README.md).

## Project Structure

```text
openapi.yaml              # backend contract (repo root) — read by frontend/orval.config.ts

frontend/
└── src/
    ├── api/
    │   ├── generated/   # orval-generated types + fetch client from openapi.yaml (do not hand-edit)
    │   ├── client.ts    # the `api` object — wraps the generated fetch client
    │   └── apiError.ts  # ApiError + toUserMessage()
    ├── components/      # Board/, Column/, Task/, common/ (Modal, ConfirmDialog, ...)
    ├── pages/           # Dashboard/, Board/
    ├── hooks/           # TanStack Query hooks (queries + optimistic mutations)
    ├── types/
    └── utils/

server/                  # FastAPI backend — see server/README.md
├── pyproject.toml       # uv-managed project + dependencies
├── uv.lock
├── src/
│   └── flowlane_api/
│       ├── routers/     # boards.py, columns.py, tasks.py — HTTP only
│       ├── services/    # positions, cascades, reorder/move rules
│       ├── repositories/# Store protocol + SqlStore (SQLAlchemy session per request)
│       ├── models/      # SQLAlchemy ORM models
│       ├── schemas/     # Pydantic models (camelCase on the wire)
│       ├── config.py    # DATABASE_URL and friends (env vars / .env)
│       ├── db.py        # engine + session factory
│       ├── dependencies.py
│       ├── errors.py    # { error: { code, message } } envelope
│       └── main.py
└── tests/               # pytest, one fresh in-memory SQLite database per test
```

## Getting Started

### Backend (start this first)

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 and all dependencies
itself on first run — no separate `pip install`).

```bash
cd server
uv run fastapi dev src/flowlane_api/main.py  # dev server with reload at http://localhost:8000
uv run pytest                                # run tests
```

Or from the repo root without changing directory:

```bash
uv --directory server run fastapi dev src/flowlane_api/main.py
```

> **Windows PowerShell 5.1** doesn't support `&&` — chain commands with `;` instead
> (`cd server; uv run fastapi dev src/flowlane_api/main.py`), or run them one at a time.

Once it's up:

- Swagger UI: http://localhost:8000/api/docs — **not** the `/docs` URL that `fastapi
  dev` prints in its banner; that one 404s because everything is mounted under `/api`
  to match `servers: [{url: /api}]` in [openapi.yaml](openapi.yaml).
- Health check: http://localhost:8000/api/health → `{"status":"ok"}`
- API base: http://localhost:8000/api (e.g. `GET /api/boards`)

Data is stored in `server/flowlane.sqlite3` (created on first start, git-ignored). Set
`DATABASE_URL` — or copy `server/.env.example` to `server/.env` — to point at a different
database; see [server/README.md](server/README.md) for the layout and configuration.

### Frontend

With the backend running, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173 and proxies `/api` requests to the backend. If the
backend isn't up, the dashboard shows an error state until it is.

## Development Phases

1. ~~Project setup~~ — frontend and backend scaffolded; database pending
2. Database + API (Board / Column / Task CRUD) — API done (contract in
   [openapi.yaml](openapi.yaml), implemented in `server/`, frontend wired to it);
   database pending
3. ~~Basic frontend~~ (dashboard, board page, task modals) — done
4. ~~Drag & drop~~ (reordering and moving tasks/columns) — done
5. ~~UX polish~~ (loading/empty/error states, search, filtering, responsive design) — done
6. Authentication (register, login, logout, protected routes)
7. Testing (unit, integration, end-to-end)
8. Deployment

Full details for each phase are in [_docs/specs.md](_docs/specs.md#19-development-phases).

## Contributing

See [AGENTS.md](AGENTS.md) for conventions to follow when working in this repo.
