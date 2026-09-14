# Mini Kanban Board --- Full-Stack Application Specification

## 1. Project Overview

Build a web-based Kanban board that allows users to manage tasks across
different stages of a workflow.

The application should allow a user to:

-   Create a board
-   Create, edit, and delete tasks
-   Organize tasks into columns
-   Drag and drop tasks between columns
-   Reorder tasks within a column
-   Assign priorities and due dates
-   Search/filter tasks
-   Persist all changes in a database

### Example workflow

``` text
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    TODO      │   │ IN PROGRESS  │   │     DONE     │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ Design UI    │   │ Build API    │   │ Setup repo   │
│              │   │              │   │              │
│ Write tests  │   │ DB schema    │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
```

------------------------------------------------------------------------

## 2. MVP Scope

Keep the first version deliberately small.

### Required MVP features

**Boards** - Create a board - View a board - Rename a board - Delete a
board

**Columns** - Default columns: - Todo - In Progress - Done - Create a
custom column - Rename a column - Delete a column - Reorder columns

**Tasks** - Create task - Edit task - Delete task - View task details -
Move task between columns - Reorder tasks - Set priority - Set due
date - Add description

**UI** - Kanban layout - Drag-and-drop - Responsive design - Loading
states - Empty states - Error states - Confirmation before destructive
actions

**Persistence** - All boards, columns, and tasks stored in a database -
Changes survive page refresh

------------------------------------------------------------------------

## 3. Stretch Features

Once the MVP works, these make excellent extensions.

### Authentication

-   Register
-   Login
-   Logout
-   Password hashing
-   Session/JWT authentication
-   User-specific boards

### Collaboration

-   Invite users to a board
-   Board roles:
    -   Owner
    -   Member
    -   Viewer
-   Multiple users working on the same board
-   Real-time updates

### Task enhancements

-   Labels/tags
-   Assignee
-   Attachments
-   Comments
-   Checklists
-   Estimated effort
-   Task activity history

### Board enhancements

-   Board background
-   Custom column colors
-   Archive completed tasks
-   Board templates

### Advanced UX

-   Keyboard shortcuts
-   Undo/redo
-   Optimistic updates
-   Dark mode
-   Mobile drag-and-drop
-   Infinite scrolling

------------------------------------------------------------------------

## 4. Data Model

A simple relational model works very well.

### User

``` text
User
----
id
email
passwordHash
name
createdAt
updatedAt
```

### Board

``` text
Board
-----
id
name
ownerId
createdAt
updatedAt
```

Relationship:

``` text
User 1 ──────── * Board
```

### Column

``` text
Column
------
id
boardId
name
position
createdAt
updatedAt
```

Relationship:

``` text
Board 1 ──────── * Column
```

### Task

``` text
Task
----
id
columnId
title
description
priority
position
dueDate
createdAt
updatedAt
```

Relationship:

``` text
Column 1 ──────── * Task
```

------------------------------------------------------------------------

## 5. Suggested Database Schema

For example, with PostgreSQL:

``` text
users
-----
id              UUID PK
email           VARCHAR UNIQUE
password_hash   VARCHAR
name            VARCHAR
created_at      TIMESTAMP
updated_at      TIMESTAMP

boards
------
id              UUID PK
name            VARCHAR
owner_id        UUID FK → users.id
created_at      TIMESTAMP
updated_at      TIMESTAMP

columns
-------
id              UUID PK
board_id        UUID FK → boards.id
name            VARCHAR
position        INTEGER
created_at      TIMESTAMP
updated_at      TIMESTAMP

tasks
-----
id              UUID PK
column_id       UUID FK → columns.id
title           VARCHAR
description     TEXT
priority        VARCHAR
position        INTEGER
due_date        TIMESTAMP NULL
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

Use a numeric `position` rather than relying on task IDs. This makes
ordering explicit.

------------------------------------------------------------------------

## 6. API Specification

A REST API is sufficient for this project.

### Boards

#### Create board

``` http
POST /api/boards
```

Request:

``` json
{
  "name": "My Project"
}
```

Response:

``` json
{
  "id": "board-123",
  "name": "My Project"
}
```

#### Get boards

``` http
GET /api/boards
```

#### Get board

``` http
GET /api/boards/:boardId
```

Response could contain the entire Kanban structure:

``` json
{
  "id": "board-123",
  "name": "My Project",
  "columns": [
    {
      "id": "column-1",
      "name": "Todo",
      "position": 0,
      "tasks": [
        {
          "id": "task-1",
          "title": "Design homepage",
          "priority": "HIGH",
          "position": 0
        }
      ]
    }
  ]
}
```

#### Update board

``` http
PATCH /api/boards/:boardId
```

#### Delete board

``` http
DELETE /api/boards/:boardId
```

------------------------------------------------------------------------

## 7. Column API

``` http
POST   /api/boards/:boardId/columns
GET    /api/boards/:boardId/columns
PATCH  /api/columns/:columnId
DELETE /api/columns/:columnId
PATCH  /api/boards/:boardId/columns/reorder
```

Example reorder request:

``` json
{
  "columnIds": [
    "column-3",
    "column-1",
    "column-2"
  ]
}
```

------------------------------------------------------------------------

## 8. Task API

``` http
POST   /api/columns/:columnId/tasks
GET    /api/tasks/:taskId
PATCH  /api/tasks/:taskId
DELETE /api/tasks/:taskId
```

Moving a task should have a dedicated endpoint:

``` http
PATCH /api/tasks/:taskId/move
```

Request:

``` json
{
  "columnId": "column-2",
  "position": 1
}
```

This means: move task X into column 2 at position 1.

------------------------------------------------------------------------

## 9. Task Object

Define the task API object roughly like this:

``` json
{
  "id": "task-123",
  "title": "Implement authentication",
  "description": "Add login and registration",
  "priority": "HIGH",
  "dueDate": "2026-09-20T00:00:00Z",
  "position": 2,
  "columnId": "column-456",
  "createdAt": "2026-09-14T12:00:00Z",
  "updatedAt": "2026-09-14T12:30:00Z"
}
```

Priority values:

``` text
LOW
MEDIUM
HIGH
```

------------------------------------------------------------------------

## 10. Frontend Screens

You don't need many screens.

### `/`

Dashboard:

``` text
My Boards

┌───────────────────────┐
│ Website Redesign      │
│ 3 columns · 12 tasks │
└───────────────────────┘

┌───────────────────────┐
│ Mobile App            │
│ 3 columns · 8 tasks  │
└───────────────────────┘

        + Create Board
```

### `/boards/:id`

Main Kanban board:

``` text
┌─────────────────────────────────────────────────────────┐
│ My Project                         🔍 Search   ⚙ Settings│
├─────────────────────────────────────────────────────────┤
│                                                         │
│ TODO             IN PROGRESS             DONE           │
│                                                         │
│ ┌─────────────┐  ┌─────────────┐       ┌─────────────┐ │
│ │ Task A      │  │ Task C      │       │ Task E      │ │
│ │ 🔴 HIGH     │  │ 🟡 MEDIUM   │       │             │ │
│ └─────────────┘  └─────────────┘       └─────────────┘ │
│                                                         │
│ ┌─────────────┐  ┌─────────────┐                       │
│ │ Task B      │  │ Task D      │                       │
│ └─────────────┘  └─────────────┘                       │
│                                                         │
│ + Add task         + Add task            + Add task     │
└─────────────────────────────────────────────────────────┘
```

### Task modal

``` text
Edit Task

Title
[ Implement authentication       ]

Description
[ Add login and registration... ]

Priority
[ High ▼ ]

Due date
[ 20 Sep 2026 ]

Column
[ In Progress ▼ ]

              Delete     Save
```

------------------------------------------------------------------------

## 11. Drag-and-Drop Requirements

The user should be able to reorder tasks within a column and move tasks
between columns.

### Within a column

``` text
A
B  ← drag
C

     ↓

A
C
B
```

### Between columns

``` text
TODO                 IN PROGRESS

A                    C
B  ───────────────→
                     B
```

When the user drops a task:

1.  Update the UI immediately.
2.  Send the new position to the backend.
3.  Persist the change.
4.  If the request fails, revert the UI and show an error.

This provides an opportunity to implement optimistic updates.

------------------------------------------------------------------------

## 12. Search and Filtering

The board should have a search box:

``` text
Search tasks...
```

Typing:

``` text
authentication
```

shows only matching tasks.

Filters:

``` text
Priority
☐ Low
☐ Medium
☐ High

Due date
☐ Overdue
☐ Due today
☐ Due this week
```

For the MVP, filtering can happen entirely on the frontend.

------------------------------------------------------------------------

## 13. Validation Rules

### Board

``` text
name:
  required
  1–100 characters
```

### Column

``` text
name:
  required
  1–50 characters
```

### Task

``` text
title:
  required
  1–200 characters

description:
  optional
  max 5000 characters

priority:
  LOW | MEDIUM | HIGH

dueDate:
  optional
  valid date
```

Validation should happen both client-side and server-side.

------------------------------------------------------------------------

## 14. Error Handling

The API should return predictable errors.

Example:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Task title is required"
  }
}
```

Useful HTTP statuses:

``` text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
500 Internal Server Error
```

The frontend should show user-friendly messages rather than raw server
errors.

------------------------------------------------------------------------

## 15. Recommended Tech Stack

### Frontend

-   React
-   TypeScript
-   Vite
-   React Router
-   TanStack Query
-   A drag-and-drop library
-   Tailwind CSS

### Backend

-   Node.js
-   TypeScript
-   Fastify or Express
-   Zod for validation

### Database

-   PostgreSQL
-   Prisma or Drizzle ORM

### Authentication

For the first version, authentication can be skipped and added in Phase
2.

### Testing

-   Vitest
-   React Testing Library
-   Playwright

### Deployment

``` text
Frontend ──────── Vercel
                    │
                    ↓
Backend ───────── Railway / Render
                    │
                    ↓
Database ───────── PostgreSQL
```

------------------------------------------------------------------------

## 16. Architecture

A clean architecture could look like:

``` text
                 ┌─────────────────┐
                 │    Browser      │
                 │ React + TS      │
                 └────────┬────────┘
                          │
                       HTTP/JSON
                          │
                          ▼
                 ┌─────────────────┐
                 │   REST API      │
                 │ Node + TS       │
                 └────────┬────────┘
                          │
                       ORM
                          │
                          ▼
                 ┌─────────────────┐
                 │   PostgreSQL    │
                 └─────────────────┘
```

### Frontend structure

``` text
src/
├── components/
│   ├── Board/
│   ├── Column/
│   ├── Task/
│   └── Modal/
├── pages/
│   ├── Dashboard/
│   └── Board/
├── hooks/
├── api/
├── types/
├── utils/
└── App.tsx
```

### Backend structure

``` text
src/
├── routes/
│   ├── boards.ts
│   ├── columns.ts
│   └── tasks.ts
├── services/
│   ├── boardService.ts
│   ├── columnService.ts
│   └── taskService.ts
├── repositories/
├── schemas/
├── middleware/
├── db/
└── server.ts
```

------------------------------------------------------------------------

## 17. Non-Functional Requirements

The application should:

-   Work on desktop and mobile
-   Have reasonable accessibility
-   Support keyboard navigation where practical
-   Avoid unnecessary API requests
-   Display loading states
-   Handle API failures gracefully
-   Never expose database credentials to the frontend
-   Validate all user input on the server
-   Prevent unauthorized access once authentication is added

------------------------------------------------------------------------

## 18. Acceptance Criteria

The MVP is complete when a user can:

-   [ ] Open the application
-   [ ] Create a board
-   [ ] Open the board
-   [ ] See Todo, In Progress, and Done columns
-   [ ] Create a task
-   [ ] Edit a task
-   [ ] Delete a task
-   [ ] Drag a task within a column
-   [ ] Drag a task to another column
-   [ ] Refresh the browser and see the same state
-   [ ] Create a custom column
-   [ ] Rename a column
-   [ ] Delete a column
-   [ ] Rename a board
-   [ ] Delete a board
-   [ ] Set task priority
-   [ ] Set a due date
-   [ ] Search tasks
-   [ ] See useful error messages
-   [ ] Use the application on a mobile-sized screen

------------------------------------------------------------------------

## 19. Development Phases

### Phase 1 --- Project setup

``` text
Frontend
Backend
Database
TypeScript
ESLint/Prettier
Git
```

### Phase 2 --- Database + API

Implement:

``` text
Board CRUD
Column CRUD
Task CRUD
```

Test everything through Postman/REST Client before building the UI.

### Phase 3 --- Basic frontend

Build:

``` text
Dashboard
Board page
Columns
Task cards
Create/edit/delete modals
```

### Phase 4 --- Drag & drop

Implement:

``` text
Task → task reordering
Task → column movement
Column → column reordering
```

### Phase 5 --- UX

Add:

``` text
Loading states
Error states
Empty states
Search
Filtering
Responsive design
Optimistic updates
```

### Phase 6 --- Authentication

Add:

``` text
Register
Login
Logout
Protected routes
User-owned boards
```

### Phase 7 --- Testing

``` text
Unit tests
API integration tests
End-to-end tests
```

### Phase 8 --- Deployment

``` text
Frontend → production
Backend → production
PostgreSQL → production
Environment variables
CORS
Database migrations
```

------------------------------------------------------------------------

## 20. Definition of Done

> **The Mini Kanban Board is considered complete when an authenticated
> user can create and manage multiple persistent Kanban boards, organize
> tasks into customizable columns, create/edit/delete tasks, reorder and
> move tasks using drag-and-drop, search and filter tasks, and use the
> application reliably across desktop and mobile devices.**

### Recommended MVP boundary

Keep real-time collaboration, comments, attachments, notifications, and
advanced permissions out of the MVP. They are excellent Phase 2
features, but adding them too early can turn a nicely scoped Kanban
project into a much larger system.
