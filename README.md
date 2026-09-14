# Flowlane

A web-based Kanban board for managing tasks across the stages of a workflow: create boards, organize work into columns, and drag and drop tasks between them.

Full specification: [_docs/specs.md](_docs/specs.md) · Backend API contract: [openapi.yaml](openapi.yaml)

**Status:** the frontend is built and runs against a mocked backend (see below); the real backend and database haven't been started yet.

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
| Backend *(not yet built)* | Python, FastAPI, Pydantic, managed with [uv](https://docs.astral.sh/uv/) — must implement `openapi.yaml` |
| Database *(not yet built)* | PostgreSQL with SQLAlchemy/SQLModel + Alembic migrations |
| Testing | Vitest, React Testing Library, Playwright (frontend, not yet written); pytest (backend) |

## Mock backend

There's no server yet, so the frontend's "backend calls" are centralized in
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

server/                  # not yet scaffolded — see "Getting Started"
├── pyproject.toml       # uv-managed project + dependencies
├── uv.lock
├── src/
│   └── flowlane_api/
│       ├── routers/     # boards.py, columns.py, tasks.py
│       ├── services/
│       ├── repositories/
│       ├── schemas/     # Pydantic models
│       ├── models/      # SQLAlchemy/SQLModel models
│       ├── db.py
│       └── main.py
├── alembic/          # migrations
└── tests/
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

### Backend (not yet built)

> This section will be filled in once the backend is scaffolded (see Phase 2 in
> [_docs/specs.md](_docs/specs.md)). It must implement [openapi.yaml](openapi.yaml).
>
> The backend will be a `uv`-managed Python project. Once scaffolded, the usual commands
> will be:
>
> ```bash
> cd server
> uv sync            # install dependencies
> uv run fastapi dev # run the dev server
> uv run pytest       # run tests
> ```

## Development Phases

1. ~~Project setup~~ — frontend done; backend/database pending
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
