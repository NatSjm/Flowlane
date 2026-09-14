# Flowlane — Frontend

React + TypeScript + Vite frontend for the Mini Kanban Board described in
[`_docs/specs.md`](../_docs/specs.md). This is the frontend only — there is
no backend yet.

## Getting started

```bash
npm install
npm run dev
```

Opens at http://localhost:5173.

## Mock backend

There is no server yet, so all "backend calls" are centralized in
[`src/api/`](src/api) and mocked:

- [`src/api/client.ts`](src/api/client.ts) exports a single `api` object with
  one async function per REST endpoint in [`../openapi.yaml`](../openapi.yaml)
  — same inputs, same outputs, same `{ error: { code, message } }` failure
  shape.
- [`src/api/mockStore.ts`](src/api/mockStore.ts) is the "database": an
  in-memory store persisted to `localStorage`, seeded with example boards so
  the app is populated on first load. Because it's `localStorage`-backed,
  state survives a page refresh, matching the spec's persistence
  requirement.
- Every write simulates ~350ms of network latency so loading states are
  visible.

**To swap in a real backend later:** replace the mock function bodies in
`src/api/client.ts` with calls into `src/api/generated/endpoints` (see
below) — real, typed `fetch` functions for every operation already exist,
they're just not called from anywhere yet. Nothing outside `src/api/` and
`src/hooks/` needs to change — all components call the backend only through
the hooks in `src/hooks/`, which call `api`.

To reset the mock data, clear the `flowlane.mockDb.v1` key from
`localStorage` (or run `localStorage.clear()`) and refresh.

## Generated API types & client (orval)

[`../openapi.yaml`](../openapi.yaml) is the source of truth for the backend
contract. [Orval](https://orval.dev) generates TypeScript from it into
`src/api/generated/` (config: [`orval.config.ts`](orval.config.ts)):

- `src/api/generated/model/` — one file per schema (`Board`, `Task`,
  `CreateTaskInput`, `Priority`, ...), including the same `minLength` /
  `maxLength` / enum constraints declared in the spec.
- `src/api/generated/endpoints/{boards,columns,tasks}/` — a real, typed
  `fetch` function per operation (`listBoards`, `createTask`, `moveTask`,
  ...), grouped the same way the spec's tags are.

After editing `openapi.yaml`, regenerate with:

```bash
npm run generate:api
```

Generated files are committed (there's no CI codegen step yet), so `git
diff` after running this will show you exactly what the contract change
touched — review it like any other diff.

**How the mock and the generated code fit together today:**
`src/types/index.ts` re-exports `Priority` from `src/api/generated/model`
and keeps the rest of the domain types (`Board`, `Column`, `Task`, ...)
hand-written but structurally identical to their generated counterparts —
the generated versions mark server-managed fields (`id`, `position`,
`createdAt`, ...) `readonly`, which is correct for API payloads but wrong
for the mock's own storage layer, which needs to mutate them.
`src/api/client.ts`'s request input types (`CreateBoardInput`,
`UpdateTaskInput`, `MoveTaskInput`, ...) *are* the generated ones directly —
the mock only ever reads those, so there's no mutability conflict, and it
means a request-shape change in `openapi.yaml` shows up as a type error at
every call site until it's handled, instead of silently drifting.

The generated `fetch` functions in `src/api/generated/endpoints` aren't
called from anywhere yet — there's no server for them to call. They're
there for when a real backend exists.

## Structure

```text
src/
├── api/
│   ├── generated/  # orval-generated types + fetch functions — see below (do not edit by hand)
│   ├── client.ts   # centralized (mocked) backend access — the `api` object
│   ├── mockStore.ts
│   └── apiError.ts
├── components/
│   ├── Board/      # dashboard board cards, board create/rename modal, search+filter bar
│   ├── Column/     # column, column header, add-column form
│   ├── Task/       # task card, add-task form, edit-task modal
│   └── common/     # Modal, ConfirmDialog, OverflowMenu, Toast, empty/error/loading states
├── pages/
│   ├── Dashboard/  # "/" — list of boards
│   └── Board/      # "/boards/:boardId" — the kanban board
├── hooks/          # TanStack Query hooks (queries + optimistic mutations)
├── types/          # domain types shared across the app
└── utils/          # validation, date helpers, id generation, board transforms
```

## What's implemented

- Boards: create, rename, delete, view (dashboard + board page).
- Columns: default Todo / In Progress / Done on new boards, create, rename
  (double-click the column name), delete, reorder via drag-and-drop.
- Tasks: create (inline "+ Add task"), edit (click a card), delete, set
  priority/due date/description, move between columns (drag-and-drop or the
  task modal's Column field), reorder within a column via drag-and-drop.
- Drag-and-drop follows the spec's optimistic-update contract: the UI
  updates immediately, the (mocked) API call persists it, and a failure
  rolls the UI back and shows a toast.
- Search (title + description) and filters (priority, overdue/due
  today/due this week), entirely client-side; drag-and-drop is disabled
  while a filter is active to avoid ambiguous positions.
- Loading, empty, and error states; confirmation dialogs before every
  destructive action; responsive layout down to mobile widths.

Authentication and other stretch features from spec §3 are intentionally
out of scope for now.
