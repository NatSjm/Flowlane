# Flowlane — Frontend

React + TypeScript + Vite frontend for the Mini Kanban Board described in
[`_docs/specs.md`](../_docs/specs.md). It talks to the FastAPI backend in
[`../server`](../server) over the REST contract in
[`../openapi.yaml`](../openapi.yaml).

## Getting started

The frontend needs the backend running — start it first (from `../server`,
see [`server/README.md`](../server/README.md)):

```bash
uv run fastapi dev src/flowlane_api/main.py
```

Then, from this directory:

```bash
npm install
npm run dev
```

Opens at http://localhost:5173. The Vite dev server proxies every `/api/*`
request to the backend at http://localhost:8000 (configured in
[`vite.config.ts`](vite.config.ts)), so the app fetches relative URLs and no
CORS setup is needed. If the backend isn't running, the dashboard shows an
error state ("Could not reach the server") until it is.

Note that the backend's store is in-memory: restarting it (including
`fastapi dev`'s auto-reload) wipes all boards, so a freshly started app
shows the empty dashboard rather than seed data.

## API layer

All "backend calls" are centralized in [`src/api/`](src/api):

- [`src/api/client.ts`](src/api/client.ts) exports a single `api` object with
  one async function per REST endpoint in [`../openapi.yaml`](../openapi.yaml).
  Each one wraps the matching generated `fetch` function (below), returns the
  2xx payload, and throws an `ApiError` otherwise — with the `code`/`message`
  from the server's `{ error: { code, message } }` envelope, or
  `NETWORK_ERROR` when the server couldn't be reached at all.
- [`src/api/apiError.ts`](src/api/apiError.ts) — `ApiError` and
  `toUserMessage()`, which the UI's error states and toasts use.
- Nothing outside `src/api/` and `src/hooks/` talks to the network — all
  components go through the TanStack Query hooks in `src/hooks/`, which
  call `api`.

## Generated API types & client (orval)

[`../openapi.yaml`](../openapi.yaml) is the source of truth for the backend
contract. [Orval](https://orval.dev) generates TypeScript from it into
`src/api/generated/` (config: [`orval.config.ts`](orval.config.ts)):

- `src/api/generated/model/` — one file per schema (`Board`, `Task`,
  `CreateTaskInput`, `Priority`, ...), including the same `minLength` /
  `maxLength` / enum constraints declared in the spec. `src/types/index.ts`
  re-exports the entity types from here, so the whole app shares the
  contract's shapes.
- `src/api/generated/endpoints/{boards,columns,tasks}/` — a typed `fetch`
  function per operation (`listBoards`, `createTask`, `moveTask`, ...),
  grouped the same way the spec's tags are, hitting `/api/...` relative
  URLs (`baseUrl` in `orval.config.ts`, matching `servers` in the contract).
  `client.ts` is the only module that calls these.

After editing `openapi.yaml`, regenerate with:

```bash
npm run generate:api
```

Generated files are committed (there's no CI codegen step yet), so `git
diff` after running this will show you exactly what the contract change
touched — review it like any other diff. Because `client.ts` and
`src/types` are built on the generated code, a request/response-shape
change shows up as a type error at every affected call site until it's
handled, instead of silently drifting.

## Structure

```text
src/
├── api/
│   ├── generated/  # orval-generated types + fetch functions — see above (do not edit by hand)
│   ├── client.ts   # centralized backend access — the `api` object
│   ├── apiError.ts
│   └── index.ts
├── components/
│   ├── Board/      # dashboard board cards, board create/rename modal, search+filter bar
│   ├── Column/     # column, column header, add-column form
│   ├── Task/       # task card, add-task form, edit-task modal
│   └── common/     # Modal, ConfirmDialog, OverflowMenu, Toast, empty/error/loading states
├── pages/
│   ├── Dashboard/  # "/" — list of boards
│   └── Board/      # "/boards/:boardId" — the kanban board
├── hooks/          # TanStack Query hooks (queries + optimistic mutations)
├── types/          # domain types (re-exported from api/generated/model)
└── utils/          # validation, date helpers, board transforms
```

## What's implemented

- Boards: create, rename, delete, view (dashboard + board page).
- Columns: default Todo / In Progress / Done on new boards, create, rename
  (double-click the column name), delete, reorder via drag-and-drop.
- Tasks: create (inline "+ Add task"), edit (click a card), delete, set
  priority/due date/description, move between columns (drag-and-drop or the
  task modal's Column field), reorder within a column via drag-and-drop.
- Drag-and-drop follows the spec's optimistic-update contract: the UI
  updates immediately, the API call persists it, and a failure rolls the UI
  back and shows a toast.
- Search (title + description) and filters (priority, overdue/due
  today/due this week), entirely client-side; drag-and-drop is disabled
  while a filter is active to avoid ambiguous positions.
- Loading, empty, and error states; confirmation dialogs before every
  destructive action; responsive layout down to mobile widths.

Authentication and other stretch features from spec §3 are intentionally
out of scope for now.
