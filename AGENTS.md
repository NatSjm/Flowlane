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
- **Backend**: not started. `frontend/src/api/generated/endpoints/` already has a real,
  typed `fetch` function per operation (generated from `openapi.yaml` by orval — see
  below); once a real backend exists, swapping the mock for those calls in `client.ts`
  should be the only frontend change required.
- **Database**: not started.

## Scope discipline

- Build the MVP defined in `_docs/specs.md` §2 before touching any stretch feature in §3
  (auth, collaboration, labels, comments, attachments, etc.). Don't add scope that isn't
  asked for.
- Follow the phase order in `_docs/specs.md` §19 (setup → DB/API → frontend → drag & drop
  → UX → auth → testing → deployment) unless the user directs otherwise. Frontend
  (Phases 1/3/4/5, against the mock) is done; a real backend is Phase 2, done retroactively.

## Tech stack

- Frontend: React + TypeScript + Vite, React Router, TanStack Query, Tailwind CSS,
  `@dnd-kit` for drag-and-drop. Implemented in `frontend/`.
- API contract & codegen: [`openapi.yaml`](openapi.yaml) at the repo root, consumed by
  [Orval](https://orval.dev) (`frontend/orval.config.ts`) to generate TypeScript types
  and typed `fetch` functions into `frontend/src/api/generated/` (run
  `npm run generate:api` from `frontend/` after editing `openapi.yaml`; generated files
  are committed, so the regeneration diff is reviewable). See "API contract changes"
  below.
- Backend (not yet built): Python + FastAPI, Pydantic for validation, managed with
  [uv](https://docs.astral.sh/uv/) (dependencies, virtualenv, and running commands —
  don't use pip/poetry/conda directly). Must implement `openapi.yaml` exactly.
- Database (not yet built): PostgreSQL via SQLAlchemy or SQLModel, with Alembic for
  migrations.
- Tests: Vitest + React Testing Library (unit/component) and Playwright (e2e) on the
  frontend — not yet written; pytest on the backend once it exists.

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

When the backend is built, use the equivalent Python layering: `routers/`, `services/`,
`repositories/`, `schemas/` (Pydantic), `models/` (SQLAlchemy/SQLModel), under
`server/src/flowlane_api/` (per `_docs/specs.md` §16).

## API contract changes

`openapi.yaml`, `frontend/src/api/client.ts` (the mock), and — once it exists — the real
backend must all agree. When a change touches the API surface:

1. Edit `openapi.yaml` first (path, schema, validation constraint, whatever changed).
2. From `frontend/`, run `npm run generate:api` to regenerate `src/api/generated/` and
   commit the diff.
3. Update `src/api/client.ts`'s mock implementation (and `mockStore.ts` if the data shape
   changed) to match.
4. Once a real backend exists, update it the same way.

Never hand-edit anything under `frontend/src/api/generated/` — it's regenerated wholesale
(`output.clean: true` in `orval.config.ts`) and hand edits will be silently discarded.

## Conventions

- TypeScript everywhere on the frontend; no implicit `any`, `noUnusedLocals`/
  `noUnusedParameters` on (see `frontend/tsconfig.app.json`). Type-hint everywhere on the
  backend, once it exists; keep `mypy`/`pyright` clean.
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
- Once the backend exists: run its commands through `uv` (`uv sync`, `uv run <cmd>`,
  `uv add <package>`) so `pyproject.toml` and `uv.lock` stay the source of truth — never
  install packages into a bare/global environment. Validate all input with Pydantic
  models server-side, even though the frontend also validates (`frontend/src/utils/
  validation.ts`) — never trust the client.

## Before committing

- Frontend: `npm run build` (runs `tsc -b` then `vite build`) and `npm run lint`
  (`oxlint`) from `frontend/` should both be clean.
- Backend (once it exists): run linting/type-checking and the test suite
  (`uv run pytest`, `uv run ruff check`, etc.).
- Confirm drag-and-drop and other destructive/stateful flows still match the "optimistic
  update, then persist, then revert on failure" behavior described in `_docs/specs.md`
  §11 (`frontend/src/hooks/useColumnMutations.ts`, `useTaskMutations.ts`).
- If `openapi.yaml` changed, confirm `frontend/src/api/generated/` was regenerated (step
  2 under "API contract changes") and the mock in `client.ts` still matches it.
- Keep commits scoped to one logical change.

## When the spec is ambiguous

Prefer the simplest choice that satisfies the MVP acceptance criteria in
`_docs/specs.md` §18. If a decision meaningfully affects data model or API shape, ask
before proceeding rather than guessing — and reflect it in `openapi.yaml`, not just code.
