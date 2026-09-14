import type { Board, Column, Task } from "../types";
import { generateId } from "../utils/id";

/**
 * In-memory "database" for the mock backend, persisted to localStorage so
 * state survives a page refresh (spec §2, "Persistence"). This file owns
 * the raw data + seed fixtures; src/api/client.ts is the only module that
 * should import it directly.
 */

interface Db {
  boards: Board[];
  columns: Column[];
  tasks: Task[];
}

const STORAGE_KEY = "flowlane.mockDb.v1";
const DEFAULT_OWNER_ID = "local-user";

function now(): string {
  return new Date().toISOString();
}

function daysFromNow(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString();
}

function seed(): Db {
  const timestamp = now();
  const websiteBoardId = generateId("board");
  const mobileBoardId = generateId("board");

  const websiteTodoId = generateId("column");
  const websiteInProgressId = generateId("column");
  const websiteDoneId = generateId("column");

  const mobileTodoId = generateId("column");
  const mobileInProgressId = generateId("column");
  const mobileDoneId = generateId("column");

  const boards: Board[] = [
    {
      id: websiteBoardId,
      name: "Website Redesign",
      ownerId: DEFAULT_OWNER_ID,
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: mobileBoardId,
      name: "Mobile App",
      ownerId: DEFAULT_OWNER_ID,
      createdAt: timestamp,
      updatedAt: timestamp,
    },
  ];

  const columns: Column[] = [
    { id: websiteTodoId, boardId: websiteBoardId, name: "Todo", position: 0, createdAt: timestamp, updatedAt: timestamp },
    { id: websiteInProgressId, boardId: websiteBoardId, name: "In Progress", position: 1, createdAt: timestamp, updatedAt: timestamp },
    { id: websiteDoneId, boardId: websiteBoardId, name: "Done", position: 2, createdAt: timestamp, updatedAt: timestamp },

    { id: mobileTodoId, boardId: mobileBoardId, name: "Todo", position: 0, createdAt: timestamp, updatedAt: timestamp },
    { id: mobileInProgressId, boardId: mobileBoardId, name: "In Progress", position: 1, createdAt: timestamp, updatedAt: timestamp },
    { id: mobileDoneId, boardId: mobileBoardId, name: "Done", position: 2, createdAt: timestamp, updatedAt: timestamp },
  ];

  const tasks: Task[] = [
    {
      id: generateId("task"),
      columnId: websiteTodoId,
      title: "Design UI",
      description: "Draft the new homepage layout and component styles.",
      priority: "HIGH",
      position: 0,
      dueDate: daysFromNow(3),
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: websiteTodoId,
      title: "Write tests",
      description: "Cover the checkout flow with integration tests.",
      priority: "MEDIUM",
      position: 1,
      dueDate: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: websiteInProgressId,
      title: "Build API",
      description: "Implement the boards/columns/tasks REST endpoints.",
      priority: "HIGH",
      position: 0,
      dueDate: daysFromNow(-1),
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: websiteInProgressId,
      title: "DB schema",
      description: "",
      priority: "MEDIUM",
      position: 1,
      dueDate: daysFromNow(1),
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: websiteDoneId,
      title: "Setup repo",
      description: "Initialize the repo, linting, and CI.",
      priority: "LOW",
      position: 0,
      dueDate: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    },

    {
      id: generateId("task"),
      columnId: mobileTodoId,
      title: "Wireframe onboarding",
      description: "",
      priority: "MEDIUM",
      position: 0,
      dueDate: daysFromNow(5),
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: mobileTodoId,
      title: "Pick navigation library",
      description: "",
      priority: "LOW",
      position: 1,
      dueDate: null,
      createdAt: timestamp,
      updatedAt: timestamp,
    },
    {
      id: generateId("task"),
      columnId: mobileInProgressId,
      title: "Auth screens",
      description: "",
      priority: "HIGH",
      position: 0,
      dueDate: daysFromNow(2),
      createdAt: timestamp,
      updatedAt: timestamp,
    },
  ];

  return { boards, columns, tasks };
}

function load(): Db {
  if (typeof localStorage === "undefined") return seed();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const fresh = seed();
      save(fresh);
      return fresh;
    }
    return JSON.parse(raw) as Db;
  } catch {
    const fresh = seed();
    save(fresh);
    return fresh;
  }
}

function save(db: Db): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  } catch {
    // Storage unavailable (private browsing, quota, etc.) — fail silently,
    // the in-memory copy still works for the rest of the session.
  }
}

let db = load();

export function getDb(): Db {
  return db;
}

export function persist(): void {
  save(db);
}

export function resetDb(): void {
  db = seed();
  save(db);
}

export { DEFAULT_OWNER_ID, now };
