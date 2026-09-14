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
  search/filter, all MVP flows from `_docs/specs.md` §2/§18. It talks to a **mock
  backend** centralized in `frontend/src/api/client.ts` (persisted to `localStorage`, no
  real network calls) that implements `openapi.yaml` exactly. See
  [`frontend/README.md`](frontend/README.md) for details.
- **Backend** (`server/`): implemented — FastAPI, every operation in `openapi.yaml`,
  tested with pytest (`server/tests/`). Persistence is an **in-memory mock store**
  (`server/src/flowlane_api/repositories/memory.py`) behind a `Store` protocol; see
  [`server/README.md`](server/README.md). The frontend is **not wired to it yet**:
  `frontend/src/api/generated/endpoints/` already has a real, typed `fetch` function per
  operation (generated from `openapi.yaml` by orval — see below), so swapping the mock
  for those calls in `client.ts` should be the only frontend change required.
- **Database**: not started — replace `InMemoryStore` with a SQL implementation of the
  same protocol (steps in `server/README.md`).

## Scope discipline

- Build the MVP defined in `_docs/specs.md` §2 before touching any stretch feature in §3
  (auth, collaboration, labels, comments, attachments, etc.). Don't add scope that isn't
  asked for.
- Follow the phase order in `_docs/specs.md` §19 (setup → DB/API → frontend → drag & drop
  → UX → auth → testing → deployment) unless the user directs otherwise. Frontend
  (Phases 1/3/4/5, against the mock) is done; the backend half of Phase 2 is done, the
  database half isn't.

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
- Database (not yet built): PostgreSQL via SQLAlchemy or SQLModel, with Alembic for
  migrations. Until then the backend uses `InMemoryStore`.
- Tests: Vitest + React Testing Library (unit/component) and Playwright (e2e) on the
  frontend — not yet written; pytest on the backend (`server/tests/`, written first,
  one fresh in-memory store per test).

### Frontend structure (implemented — `frontend/src/`)

```text
src/
├── api/
│   ├── generated/   # orval output from ../../openapi.yaml — do not hand-edit, regenerate instead
│   ├── client.ts    # the `api` object — mock backend, mirrors openapi.yaml exactly
│   ├── mockStore.ts # localStorage-backed "database" + seed data
│   └── apiError.ts
├── components/
│   ├── Board/       # dashboard cards, board create/rename modal, search+filter bar
│   ├── Column/      # Column, ColumnHeader, AddColumnForm
│   ├── Task/        # TaskCard, AddTaskForm, TaskModal
│   └── common/      # Modal, ConfirmDialog, OverflowMenu, ToastProvider, empty/error/loading states
├── pages/
│   ├── Dashboard/   # "/"
│   └── Board/       # "/boards/:boardId"
├── hooks/           # TanStack Query hooks — queries + optimistic mutations, call `api`
├── types/           # domain types (Priority re-exported from api/generated/model; entities hand-written — see types/index.ts for why)
└── utils/           # validation, date helpers, id generation, board transforms (optimistic-update logic)
```

### Backend structure (implemented — `server/src/flowlane_api/`)

Same layering in Python (per `_docs/specs.md` §16): `routers/` (HTTP only) →
`services/` (rules: positions, cascades, reorder/move) → `repositories/` (`Store`
protocol, `InMemoryStore` mock, plain-dataclass records), with `schemas/` for Pydantic
request/response models and `errors.py` for the error envelope. `models/` (ORM) doesn't
exist yet — it arrives with the database. Details in `server/README.md`.

## API contract changes

`openapi.yaml`, `frontend/src/api/client.ts` (the mock), and — once it exists — the real
backend must all agree. When a change touches the API surface:

1. Edit `openapi.yaml` first (path, schema, validation constraint, whatever changed).
2. From `frontend/`, run `npm run generate:api` to regenerate `src/api/generated/` and
   commit the diff.
3. Update `src/api/client.ts`'s mock implementation (and `mockStore.ts` if the data shape
   changed) to match.
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
  `{ "error": { "code": "...", "message": "..." } }`. The mock only emits
  `VALIDATION_ERROR` and `NOT_FOUND`; a real backend can add more codes but must keep the
  same envelope (`frontend/src/api/apiError.ts` only reads `code`/`message`).
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
  2 under "API contract changes") and the mock in `client.ts` still matches it.
- Keep commits scoped to one logical change.

## Running the backend

`cd server` then `uv run fastapi dev src/flowlane_api/main.py` (or, from the root,
`uv --directory server run fastapi dev src/flowlane_api/main.py`). Details and URLs in
[`server/README.md`](server/README.md); the two things that trip people up:

- Everything is mounted under `/api` (`servers: [{url: /api}]` in `openapi.yaml`), so
  Swagger is at `http://localhost:8000/api/docs`, **not** the `/docs` URL that
  `fastapi dev` prints in its banner. A 404 on `GET /docs` in the logs is expected.
- The store is in-memory: every restart — including `fastapi dev`'s auto-reload on a
  source change — wipes all boards. Don't treat lost data as a bug.

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
