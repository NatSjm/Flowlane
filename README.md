# Flowlane

A web-based Kanban board for managing tasks across the stages of a workflow: create boards, organize work into columns, and drag and drop tasks between them.

Full specification: [_docs/specs.md](_docs/specs.md) · Backend API contract: [openapi.yaml](openapi.yaml)

**Status:** the frontend is built and runs against a mocked backend (see below). The real backend (`server/`) implements `openapi.yaml` with an in-memory mock database; the frontend isn't wired to it yet, and the real database hasn't been started.

## Features (MVP)

- Create, view, rename, and delete boards
- Default columns (Todo / In Progress / Done) plus custom columns — create, rename, delete, reorder
- Create, edit, delete, and view tasks with priority, due date, and description
- Drag and drop to reorder tasks within a column and move tasks between columns
- Search and filter tasks
- State survives a page refresh (currently via a `localStorage`-backed mock — see
  "Mock backend" below; will move to a real database once the backend exists)

See [_docs/specs.md](_docs/specs.md) for stretch features (auth, collaboration, labels, comments, etc.) and the full data model, API, and phased build plan.

## Tech Stack

| Layer | Choice |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS, `@dnd-kit` |
| API contract & codegen | [openapi.yaml](openapi.yaml), consumed by [Orval](https://orval.dev) to generate frontend types + a typed `fetch` client |
| Backend | Python, FastAPI, Pydantic, managed with [uv](https://docs.astral.sh/uv/) — implements `openapi.yaml` (see [server/README.md](server/README.md)) |
| Database *(not yet built)* | PostgreSQL with SQLAlchemy/SQLModel + Alembic migrations — the backend currently uses an in-memory mock store |
| Testing | Vitest, React Testing Library, Playwright (frontend, not yet written); pytest (backend) |

## Mock backend

The frontend isn't wired to the server yet, so its "backend calls" are centralized in
[`frontend/src/api/client.ts`](frontend/src/api/client.ts) and mocked: an in-memory
store persisted to `localStorage` that implements [openapi.yaml](openapi.yaml) exactly
— same requests, responses, and error shape a real backend will return. See
[frontend/README.md](frontend/README.md) for how it works and how to swap in a real
backend later.

## Project Structure

```text
openapi.yaml              # backend contract (repo root) — read by frontend/orval.config.ts

frontend/
└── src/
    ├── api/
    │   ├── generated/   # orval-generated types + fetch client from openapi.yaml (do not hand-edit)
    │   ├── client.ts    # the `api` object — mock backend for now
    │   └── mockStore.ts # localStorage-backed "database" + seed data
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
│       ├── repositories/# Store protocol + InMemoryStore (mock DB; SQL impl comes later)
│       ├── schemas/     # Pydantic models (camelCase on the wire)
│       ├── dependencies.py
│       ├── errors.py    # { error: { code, message } } envelope
│       └── main.py
└── tests/               # pytest, one fresh in-memory store per test
```

## Getting Started

### Frontend (works today)

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173. No backend or database required — see "Mock backend"
above.

### Backend

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

Data lives in memory and is lost on every restart — including `fastapi dev`'s
auto-reload when a source file changes. See [server/README.md](server/README.md) for the
layout and how the mock store will be replaced by a real database.

## Development Phases

1. ~~Project setup~~ — frontend and backend scaffolded; database pending
2. Database + API (Board / Column / Task CRUD) — contract specified in
   [openapi.yaml](openapi.yaml) and implemented by the frontend's mock; real
   implementation pending
3. ~~Basic frontend~~ (dashboard, board page, task modals) — done
4. ~~Drag & drop~~ (reordering and moving tasks/columns) — done
5. ~~UX polish~~ (loading/empty/error states, search, filtering, responsive design) — done
6. Authentication (register, login, logout, protected routes)
7. Testing (unit, integration, end-to-end)
8. Deployment

Full details for each phase are in [_docs/specs.md](_docs/specs.md#19-development-phases).

## Contributing

See [AGENTS.md](AGENTS.md) for conventions to follow when working in this repo.
