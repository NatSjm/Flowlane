import type { Board, BoardDetail, BoardSummary, Column, ColumnWithTasks, Task } from "../types";
import { ApiError } from "./apiError";
import { DEFAULT_OWNER_ID, getDb, now, persist } from "./mockStore";
import { generateId } from "../utils/id";
import {
  validateBoardName,
  validateColumnName,
  validateDueDate,
  validateTaskDescription,
  validateTaskTitle,
} from "../utils/validation";
import type { CreateBoardInput as GeneratedCreateBoardInput } from "./generated/model/createBoardInput";
import type { UpdateBoardInput as GeneratedUpdateBoardInput } from "./generated/model/updateBoardInput";
import type { CreateColumnInput as GeneratedCreateColumnInput } from "./generated/model/createColumnInput";
import type { UpdateColumnInput as GeneratedUpdateColumnInput } from "./generated/model/updateColumnInput";
import type { CreateTaskInput as GeneratedCreateTaskInput } from "./generated/model/createTaskInput";
import type { UpdateTaskInput as GeneratedUpdateTaskInput } from "./generated/model/updateTaskInput";
import type { MoveTaskInput as GeneratedMoveTaskInput } from "./generated/model/moveTaskInput";

/**
 * ============================================================================
 * Centralized backend access point.
 *
 * Every network call the frontend makes goes through this module. It is
 * currently backed by a mock (an in-memory store persisted to localStorage,
 * see ./mockStore) that mirrors the REST contract in ../../../openapi.yaml
 * (§6-9 of `_docs/specs.md`, which that file was written from): same
 * function shapes, same request/response payloads, same
 * `{ error: { code, message } }` failure shape and artificial latency.
 *
 * openapi.yaml is the source of truth for the request/response types below —
 * they're re-exports of ./generated/model, generated from it by orval
 * (`npm run generate:api`; see orval.config.ts). ./generated/endpoints has
 * real, typed `fetch` functions for every operation, generated the same way
 * but not called from here yet, since there's no backend for them to call.
 * When the real API is ready, swap the mock implementations below for calls
 * into ./generated/endpoints — nothing outside src/api/ and src/hooks/
 * should need to change.
 * ============================================================================
 */

const LATENCY_MS = 350;

function delay(ms: number = LATENCY_MS): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function fail(code: string, message: string): never {
  throw new ApiError(code, message);
}

function assertValid(message: string | null): void {
  if (message) fail("VALIDATION_ERROR", message);
}

// ---------------------------------------------------------------------------
// Boards
// ---------------------------------------------------------------------------

export type CreateBoardInput = GeneratedCreateBoardInput;
export type UpdateBoardInput = GeneratedUpdateBoardInput;

async function listBoards(): Promise<BoardSummary[]> {
  await delay();
  const db = getDb();
  return db.boards
    .map((board) => summarizeBoard(board))
    .sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

async function getBoard(boardId: string): Promise<BoardDetail> {
  await delay();
  const db = getDb();
  const board = db.boards.find((b) => b.id === boardId);
  if (!board) fail("NOT_FOUND", "Board not found");

  const columns: ColumnWithTasks[] = db.columns
    .filter((c) => c.boardId === boardId)
    .sort((a, b) => a.position - b.position)
    .map((column) => ({
      ...column,
      tasks: db.tasks
        .filter((t) => t.columnId === column.id)
        .sort((a, b) => a.position - b.position),
    }));

  return { ...board, columns };
}

async function createBoard(input: CreateBoardInput): Promise<Board> {
  await delay();
  assertValid(validateBoardName(input.name));
  const db = getDb();
  const timestamp = now();
  const board: Board = {
    id: generateId("board"),
    name: input.name.trim(),
    ownerId: DEFAULT_OWNER_ID,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
  db.boards.push(board);

  // New boards start with the default Todo / In Progress / Done columns
  // (spec §2, "Columns").
  ["Todo", "In Progress", "Done"].forEach((name, position) => {
    db.columns.push({
      id: generateId("column"),
      boardId: board.id,
      name,
      position,
      createdAt: timestamp,
      updatedAt: timestamp,
    });
  });

  persist();
  return board;
}

async function updateBoard(boardId: string, input: UpdateBoardInput): Promise<Board> {
  await delay();
  assertValid(validateBoardName(input.name));
  const db = getDb();
  const board = db.boards.find((b) => b.id === boardId);
  if (!board) fail("NOT_FOUND", "Board not found");
  board.name = input.name.trim();
  board.updatedAt = now();
  persist();
  return board;
}

async function deleteBoard(boardId: string): Promise<void> {
  await delay();
  const db = getDb();
  const index = db.boards.findIndex((b) => b.id === boardId);
  if (index === -1) fail("NOT_FOUND", "Board not found");
  db.boards.splice(index, 1);
  const columnIds = db.columns.filter((c) => c.boardId === boardId).map((c) => c.id);
  db.columns = db.columns.filter((c) => c.boardId !== boardId);
  db.tasks = db.tasks.filter((t) => !columnIds.includes(t.columnId));
  persist();
}

function summarizeBoard(board: Board): BoardSummary {
  const db = getDb();
  const columns = db.columns.filter((c) => c.boardId === board.id);
  const columnIds = columns.map((c) => c.id);
  const taskCount = db.tasks.filter((t) => columnIds.includes(t.columnId)).length;
  return { ...board, columnCount: columns.length, taskCount };
}

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

export type CreateColumnInput = GeneratedCreateColumnInput;
export type UpdateColumnInput = GeneratedUpdateColumnInput;

async function createColumn(boardId: string, input: CreateColumnInput): Promise<Column> {
  await delay();
  assertValid(validateColumnName(input.name));
  const db = getDb();
  const board = db.boards.find((b) => b.id === boardId);
  if (!board) fail("NOT_FOUND", "Board not found");

  const siblings = db.columns.filter((c) => c.boardId === boardId);
  const timestamp = now();
  const column: Column = {
    id: generateId("column"),
    boardId,
    name: input.name.trim(),
    position: siblings.length,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
  db.columns.push(column);
  persist();
  return column;
}

async function updateColumn(columnId: string, input: UpdateColumnInput): Promise<Column> {
  await delay();
  assertValid(validateColumnName(input.name));
  const db = getDb();
  const column = db.columns.find((c) => c.id === columnId);
  if (!column) fail("NOT_FOUND", "Column not found");
  column.name = input.name.trim();
  column.updatedAt = now();
  persist();
  return column;
}

async function deleteColumn(columnId: string): Promise<void> {
  await delay();
  const db = getDb();
  const column = db.columns.find((c) => c.id === columnId);
  if (!column) fail("NOT_FOUND", "Column not found");

  db.columns = db.columns.filter((c) => c.id !== columnId);
  db.tasks = db.tasks.filter((t) => t.columnId !== columnId);

  // Reindex the remaining columns so positions stay contiguous.
  db.columns
    .filter((c) => c.boardId === column.boardId)
    .sort((a, b) => a.position - b.position)
    .forEach((c, index) => {
      c.position = index;
    });

  persist();
}

async function reorderColumns(boardId: string, columnIds: string[]): Promise<Column[]> {
  await delay();
  const db = getDb();
  columnIds.forEach((columnId, index) => {
    const column = db.columns.find((c) => c.id === columnId && c.boardId === boardId);
    if (!column) fail("NOT_FOUND", "Column not found");
    column.position = index;
    column.updatedAt = now();
  });
  persist();
  return db.columns.filter((c) => c.boardId === boardId).sort((a, b) => a.position - b.position);
}

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

export type CreateTaskInput = GeneratedCreateTaskInput;
export type UpdateTaskInput = GeneratedUpdateTaskInput;
export type MoveTaskInput = GeneratedMoveTaskInput;

function reindexColumn(columnId: string): void {
  const db = getDb();
  db.tasks
    .filter((t) => t.columnId === columnId)
    .sort((a, b) => a.position - b.position)
    .forEach((t, index) => {
      t.position = index;
    });
}

async function createTask(columnId: string, input: CreateTaskInput): Promise<Task> {
  await delay();
  assertValid(validateTaskTitle(input.title));
  assertValid(validateTaskDescription(input.description ?? ""));
  assertValid(validateDueDate(input.dueDate ?? null));

  const db = getDb();
  const column = db.columns.find((c) => c.id === columnId);
  if (!column) fail("NOT_FOUND", "Column not found");

  const siblings = db.tasks.filter((t) => t.columnId === columnId);
  const timestamp = now();
  const task: Task = {
    id: generateId("task"),
    columnId,
    title: input.title.trim(),
    description: input.description?.trim() ?? "",
    priority: input.priority ?? "MEDIUM",
    position: siblings.length,
    dueDate: input.dueDate ?? null,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
  db.tasks.push(task);
  persist();
  return task;
}

async function getTask(taskId: string): Promise<Task> {
  await delay();
  const db = getDb();
  const task = db.tasks.find((t) => t.id === taskId);
  if (!task) fail("NOT_FOUND", "Task not found");
  return task;
}

async function updateTask(taskId: string, input: UpdateTaskInput): Promise<Task> {
  await delay();
  if (input.title !== undefined) assertValid(validateTaskTitle(input.title));
  if (input.description !== undefined) assertValid(validateTaskDescription(input.description));
  if (input.dueDate !== undefined) assertValid(validateDueDate(input.dueDate));

  const db = getDb();
  const task = db.tasks.find((t) => t.id === taskId);
  if (!task) fail("NOT_FOUND", "Task not found");

  if (input.columnId !== undefined && input.columnId !== task.columnId) {
    const targetColumn = db.columns.find((c) => c.id === input.columnId);
    if (!targetColumn) fail("NOT_FOUND", "Column not found");
    const previousColumnId = task.columnId;
    task.columnId = input.columnId;
    task.position = db.tasks.filter((t) => t.columnId === input.columnId).length;
    reindexColumn(previousColumnId);
  }

  if (input.title !== undefined) task.title = input.title.trim();
  if (input.description !== undefined) task.description = input.description.trim();
  if (input.priority !== undefined) task.priority = input.priority;
  if (input.dueDate !== undefined) task.dueDate = input.dueDate;
  task.updatedAt = now();

  persist();
  return task;
}

async function deleteTask(taskId: string): Promise<void> {
  await delay();
  const db = getDb();
  const task = db.tasks.find((t) => t.id === taskId);
  if (!task) fail("NOT_FOUND", "Task not found");
  db.tasks = db.tasks.filter((t) => t.id !== taskId);
  reindexColumn(task.columnId);
  persist();
}

async function moveTask(taskId: string, input: MoveTaskInput): Promise<Task> {
  await delay(150); // snappier than other writes — this backs drag-and-drop
  const db = getDb();
  const task = db.tasks.find((t) => t.id === taskId);
  if (!task) fail("NOT_FOUND", "Task not found");
  const targetColumn = db.columns.find((c) => c.id === input.columnId);
  if (!targetColumn) fail("NOT_FOUND", "Column not found");

  const sourceColumnId = task.columnId;
  const destinationTasks = db.tasks
    .filter((t) => t.columnId === input.columnId && t.id !== taskId)
    .sort((a, b) => a.position - b.position);

  const clampedPosition = Math.max(0, Math.min(input.position, destinationTasks.length));
  destinationTasks.splice(clampedPosition, 0, task);

  task.columnId = input.columnId;
  task.updatedAt = now();
  destinationTasks.forEach((t, index) => {
    t.position = index;
  });

  if (sourceColumnId !== input.columnId) {
    reindexColumn(sourceColumnId);
  }

  persist();
  return task;
}

// ---------------------------------------------------------------------------

export const api = {
  listBoards,
  getBoard,
  createBoard,
  updateBoard,
  deleteBoard,
  createColumn,
  updateColumn,
  deleteColumn,
  reorderColumns,
  createTask,
  getTask,
  updateTask,
  deleteTask,
  moveTask,
};

export type Api = typeof api;
