# AGENTS.md

Guidance for AI coding agents (and human contributors) working in this repository.

## Project

Flowlane is a full-stack Kanban board application. The authoritative specification —
data model, API contract, validation rules, UI screens, and acceptance criteria — lives
in [_docs/specs.md](_docs/specs.md). Read it before making product or architecture
decisions; this file only covers how to work in the repo, not what to build.

## Scope discipline

- Build the MVP defined in `_docs/specs.md` §2 before touching any stretch feature in §3
  (auth, collaboration, labels, comments, attachments, etc.). Don't add scope that isn't
  asked for.
- Follow the phase order in `_docs/specs.md` §19 (setup → DB/API → frontend → drag & drop
  → UX → auth → testing → deployment) unless the user directs otherwise.

## Tech stack

- Frontend: React + TypeScript + Vite, React Router, TanStack Query, Tailwind CSS.
- Backend: Python + FastAPI, Pydantic for validation, managed with
  [uv](https://docs.astral.sh/uv/) (dependencies, virtualenv, and running commands —
  don't use pip/poetry/conda directly).
- Database: PostgreSQL via SQLAlchemy or SQLModel, with Alembic for migrations.
- Tests: Vitest + React Testing Library (unit/component) and Playwright (e2e) on the
  frontend; pytest on the backend.

Match the structure in `_docs/specs.md` §16 for new frontend files (`components/`,
`pages/`, `hooks/`, `api/`). On the backend, use the equivalent Python layering:
`routers/`, `services/`, `repositories/`, `schemas/` (Pydantic), `models/`
(SQLAlchemy/SQLModel), under `server/src/flowlane_api/`.

## Conventions

- TypeScript everywhere on the frontend; no implicit `any`. Type-hint everywhere on the
  backend; keep `mypy`/`pyright` clean.
- Run backend commands through `uv` (`uv sync`, `uv run <cmd>`, `uv add <package>`) so
  `pyproject.toml` and `uv.lock` stay the source of truth — never install packages into
  a bare/global environment.
- Validate all input with Pydantic models on the server, even if the client also
  validates. Never trust the client.
- Use a numeric `position` field for ordering columns and tasks (per `_docs/specs.md`
  §5) — never rely on array/list index or ID order.
- API errors follow the shape in `_docs/specs.md` §14:
  `{ "error": { "code": "...", "message": "..." } }` with predictable HTTP status codes
  (use FastAPI exception handlers to normalize this instead of returning raw tracebacks).
- Task priority is one of `LOW | MEDIUM | HIGH` — keep it an enum on both sides (a
  Python `Enum`/`StrEnum` in Pydantic models, a union type in TypeScript), not a free
  string.
- Never expose database credentials or secrets to the frontend; keep them in
  server-side environment variables only (see `.gitignore` — `.env*` files are excluded
  except `.env.example`).

## Before committing

- Run linting/type-checking and the test suite for whatever part of the stack you
  touched (`uv run pytest`, `uv run ruff check`, etc. on the backend).
- Confirm drag-and-drop and other destructive/stateful flows still match the "optimistic
  update, then persist, then revert on failure" behavior described in
  `_docs/specs.md` §11.
- Keep commits scoped to one logical change.

## When the spec is ambiguous

Prefer the simplest choice that satisfies the MVP acceptance criteria in
`_docs/specs.md` §18. If a decision meaningfully affects data model or API shape, ask
before proceeding rather than guessing.
