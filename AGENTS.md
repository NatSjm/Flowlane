# AGENTS.md

Guidance for AI coding agents (and human contributors) working in this repository.

## Project

Flowlane is a full-stack Kanban board application.

- [`_docs/specs.md`](_docs/specs.md) is the product spec: data model, UI screens,
  validation rules, and acceptance criteria.
- [`openapi.yaml`](openapi.yaml) (repo root) is the authoritative **backend contract**
  — every endpoint, method, path, request/response schema, and auth requirement the
  frontend expects. It was derived from `_docs/specs.md` §6-9 but is more precise; when
  implementing or changing an API, treat `openapi.yaml` as the source of truth and keep
  `_docs/specs.md` in mind for product behavior.

Read both before making product or architecture decisions; this file only covers how to
work in the repo, not what to build.

## Current state

- **Frontend** (`frontend/`): implemented — dashboard, board page, drag-and-drop,
  search/filter, all MVP flows from `_docs/specs.md` §2/§18. It talks to the real
  backend through `frontend/src/api/client.ts`, which wraps the orval-generated `fetch`
  functions in `frontend/src/api/generated/endpoints/` (relative `/api` URLs; the Vite
  dev server proxies them to port 8000 — `frontend/vite.config.ts`). See
  [`frontend/README.md`](frontend/README.md) for details.
- **Backend** (`server/`): implemented — FastAPI, every operation in `openapi.yaml`,
  tested with pytest (`server/tests/`). The frontend must be run against it — there
  is no longer a frontend-side mock.
- **Database**: SQLAlchemy behind a `Store` protocol
  (`server/src/flowlane_api/repositories/sql.py`, ORM models in `models/`). The
  backend is chosen by `DATABASE_URL`; the default is a SQLite file
  (`server/flowlane.sqlite3`). Schema is created with `create_all` on startup — no
  Alembic yet, no PostgreSQL driver installed yet; see "Database" in
  [`server/README.md`](server/README.md).

## Scope discipline

- Build the MVP defined in `_docs/specs.md` §2 before touching any stretch feature in §3
  (auth, collaboration, labels, comments, attachments, etc.). Don't add scope that isn't
  asked for.
- Follow the phase order in `_docs/specs.md` §19 (setup → DB/API → frontend → drag & drop
  → UX → auth → testing → deployment) unless the user directs otherwise. Frontend
  (Phases 1/3/4/5) and Phase 2 (API + SQLite database) are done; migrations (Alembic)
  and PostgreSQL support are the remaining database work.

## Tech stack

- Frontend: React + TypeScript + Vite, React Router, TanStack Query, Tailwind CSS,
  `@dnd-kit` for drag-and-drop. Implemented in `frontend/`.
- API contract & codegen: [`openapi.yaml`](openapi.yaml) at the repo root, consumed by
  [Orval](https://orval.dev) (`frontend/orval.config.ts`) to generate TypeScript types
  and typed `fetch` functions into `frontend/src/api/generated/` (run
  `npm run generate:api` from `frontend/` after editing `openapi.yaml`; generated files
  are committed, so the regeneration diff is reviewable). See "API contract changes"
  below.
- Backend (`server/`): Python 3.12 + FastAPI, Pydantic for validation, managed with
  [uv](https://docs.astral.sh/uv/) (dependencies, virtualenv, and running commands —
  don't use pip/poetry/conda directly). Implements `openapi.yaml` exactly.
- Database: SQLAlchemy 2 (mapped dataclasses), SQLite by default, configured with the
  `DATABASE_URL` environment variable (`server/.env.example`). Keep the models and
  queries dialect-agnostic — PostgreSQL is planned, and Alembic migrations with it.
  SQLite-specific engine tweaks belong in `server/src/flowlane_api/db.py` only.
- Tests: Vitest + React Testing Library (unit/component) and Playwright (e2e) on the
  frontend — not yet written; pytest on the backend (`server/tests/`, written first,
  one fresh in-memory SQLite database per test).

### Frontend structure (implemented — `frontend/src/`)

```text
src/
├── api/
│   ├── generated/   # orval output from ../../openapi.yaml — do not hand-edit, regenerate instead
│   ├── client.ts    # the `api` object — wraps generated/endpoints, throws ApiError on non-2xx
│   ├── apiError.ts  # ApiError + toUserMessage()
│   └── index.ts
├── components/
│   ├── Board/       # dashboard cards, board create/rename modal, search+filter bar
│   ├── Column/      # Column, ColumnHeader, AddColumnForm
│   ├── Task/        # TaskCard, AddTaskForm, TaskModal
│   └── common/      # Modal, ConfirmDialog, OverflowMenu, ToastProvider, empty/error/loading states
├── pages/
│   ├── Dashboard/   # "/"
│   └── Board/       # "/boards/:boardId"
├── hooks/           # TanStack Query hooks — queries + optimistic mutations, call `api`
├── types/           # domain types, re-exported from api/generated/model
└── utils/           # validation, date helpers, board transforms (optimistic-update logic)
```

### Backend structure (implemented — `server/src/flowlane_api/`)

Same layering in Python (per `_docs/specs.md` §16): `routers/` (HTTP only) →
`services/` (rules: positions, cascades, reorder/move) → `repositories/` (`Store`
protocol, `SqlStore` on a per-request SQLAlchemy session) → `models/` (ORM mapped
dataclasses: `BoardRecord`, `ColumnRecord`, `TaskRecord`), with `schemas/` for Pydantic
request/response models, `errors.py` for the error envelope, `config.py` for settings
and `db.py` for engine/session setup. Details in `server/README.md`.

## API contract changes

`openapi.yaml`, the frontend, and the backend must all agree. When a change touches the
API surface:

1. Edit `openapi.yaml` first (path, schema, validation constraint, whatever changed).
2. From `frontend/`, run `npm run generate:api` to regenerate `src/api/generated/` and
   commit the diff.
3. Fix whatever the regenerated types break in `src/api/client.ts`, `src/hooks/`, and
   `src/types/` (a shape change surfaces as type errors there).
4. Update the backend (`server/src/flowlane_api/schemas/`, `routers/`, `services/`) and
   its tests the same way; `uv run pytest` from `server/` must pass.

Never hand-edit anything under `frontend/src/api/generated/` — it's regenerated wholesale
(`output.clean: true` in `orval.config.ts`) and hand edits will be silently discarded.

## Conventions

- TypeScript everywhere on the frontend; no implicit `any`, `noUnusedLocals`/
  `noUnusedParameters` on (see `frontend/tsconfig.app.json`). Type-hint everywhere on the
  backend; keep `mypy --strict` clean (`uv run mypy src tests` from `server/`).
- Use a numeric `position` field for ordering columns and tasks (per `_docs/specs.md`
  §5 and `openapi.yaml`) — never rely on array/list index or ID order. `position` is
  server-managed (`readOnly` in the schema); clients only influence it through the
  reorder/move endpoints.
- API errors follow the shape in `_docs/specs.md` §14 / `openapi.yaml`'s `Error` schema:
  `{ "error": { "code": "...", "message": "..." } }`. The backend emits
  `VALIDATION_ERROR`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, and `INTERNAL_ERROR`; new codes
  are fine as long as the envelope stays (`frontend/src/api/client.ts` only reads
  `code`/`message`, and adds its own `NETWORK_ERROR` when no response arrives).
- Task priority is one of `LOW | MEDIUM | HIGH` — keep it an enum on both sides (the
  generated `Priority` type/const on the frontend; a Python `Enum`/`StrEnum` in Pydantic
  models on the backend), not a free string.
- Never expose database credentials or secrets to the frontend; keep them in
  server-side environment variables only (see `.gitignore` — `.env*` files are excluded
  except `.env.example`).
- Backend: run its commands through `uv` (`uv sync`, `uv run <cmd>`,
  `uv add <package>`) so `pyproject.toml` and `uv.lock` stay the source of truth — never
  install packages into a bare/global environment. Validate all input with Pydantic
  models server-side, even though the frontend also validates (`frontend/src/utils/
  validation.ts`) — never trust the client.

## Before committing

- Frontend: `npm run build` (runs `tsc -b` then `vite build`) and `npm run lint`
  (`oxlint`) from `frontend/` should both be clean.
- Backend: from `server/`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format
  --check .`, and `uv run mypy src tests` should all be clean.
- Confirm drag-and-drop and other destructive/stateful flows still match the "optimistic
  update, then persist, then revert on failure" behavior described in `_docs/specs.md`
  §11 (`frontend/src/hooks/useColumnMutations.ts`, `useTaskMutations.ts`).
- If `openapi.yaml` changed, confirm `frontend/src/api/generated/` was regenerated (step
  2 under "API contract changes") and `client.ts` still type-checks against it.
- Keep commits scoped to one logical change.

## Running the backend

`cd server` then `uv run fastapi dev src/flowlane_api/main.py` (or, from the root,
`uv --directory server run fastapi dev src/flowlane_api/main.py`). Details and URLs in
[`server/README.md`](server/README.md); the two things that trip people up:

- Everything is mounted under `/api` (`servers: [{url: /api}]` in `openapi.yaml`), so
  Swagger is at `http://localhost:8000/api/docs`, **not** the `/docs` URL that
  `fastapi dev` prints in its banner. A 404 on `GET /docs` in the logs is expected.
- Data lives in `server/flowlane.sqlite3` (git-ignored) unless `DATABASE_URL` says
  otherwise, and survives restarts. There are no migrations yet: after changing a
  model, delete the file so `create_all` rebuilds the schema.

## Shell notes

This project is developed on Windows. When suggesting commands to the user, remember
that **Windows PowerShell 5.1 does not support `&&`** — chain with `;` (or give one
command per block). `&&` works in PowerShell 7+, Git Bash, and the Bash tool, so it's
fine inside scripts you run yourself; it's the copy-pasteable snippets that must avoid
it. Use forward slashes in paths passed to `uv`/`fastapi` (they work everywhere).

## When the spec is ambiguous

Prefer the simplest choice that satisfies the MVP acceptance criteria in
`_docs/specs.md` §18. If a decision meaningfully affects data model or API shape, ask
before proceeding rather than guessing — and reflect it in `openapi.yaml`, not just code.
