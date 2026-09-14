# Flowlane

A web-based Kanban board for managing tasks across the stages of a workflow: create boards, organize work into columns, and drag and drop tasks between them.

Full specification: [_docs/specs.md](_docs/specs.md)

## Features (MVP)

- Create, view, rename, and delete boards
- Default columns (Todo / In Progress / Done) plus custom columns — create, rename, delete, reorder
- Create, edit, delete, and view tasks with priority, due date, and description
- Drag and drop to reorder tasks within a column and move tasks between columns
- Search and filter tasks
- All data persisted in a database; state survives a page refresh

See [_docs/specs.md](_docs/specs.md) for stretch features (auth, collaboration, labels, comments, etc.) and the full data model, API, and phased build plan.

## Tech Stack

| Layer | Choice |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, managed with [uv](https://docs.astral.sh/uv/) |
| Database | PostgreSQL with SQLAlchemy/SQLModel + Alembic migrations |
| Testing | Vitest, React Testing Library, Playwright (frontend); pytest (backend) |

## Project Structure

```text
src/
├── components/   # Board, Column, Task, Modal
├── pages/        # Dashboard, Board
├── hooks/
├── api/
├── types/
└── utils/

server/
├── pyproject.toml   # uv-managed project + dependencies
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

> Project scaffolding is not yet in place — this section will be filled in once the frontend and backend apps are initialized (see Phase 1 in [_docs/specs.md](_docs/specs.md)).
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

1. Project setup (frontend, backend, database, TypeScript/Python, linting)
2. Database + API (Board / Column / Task CRUD)
3. Basic frontend (dashboard, board page, task modals)
4. Drag & drop (reordering and moving tasks/columns)
5. UX polish (loading/empty/error states, search, filtering, responsive design)
6. Authentication (register, login, logout, protected routes)
7. Testing (unit, integration, end-to-end)
8. Deployment

Full details for each phase are in [_docs/specs.md](_docs/specs.md#19-development-phases).

## Contributing

See [AGENTS.md](AGENTS.md) for conventions to follow when working in this repo.
