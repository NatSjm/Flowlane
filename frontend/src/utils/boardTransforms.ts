import type { BoardDetail, Column, ColumnWithTasks, Priority, Task } from "../types";

/**
 * Pure, immutable transforms over a BoardDetail. Used by the optimistic
 * update path in src/hooks/* so the UI reflects a drag/edit instantly,
 * before the network call resolves — mirroring the position bookkeeping
 * the server applies for real (server/src/flowlane_api/services/).
 */

export function withColumnAdded(board: BoardDetail, column: Column): BoardDetail {
  return { ...board, columns: [...board.columns, { ...column, tasks: [] }] };
}

export function withColumnRenamed(board: BoardDetail, columnId: string, name: string): BoardDetail {
  return {
    ...board,
    columns: board.columns.map((c) => (c.id === columnId ? { ...c, name } : c)),
  };
}

export function withColumnRemoved(board: BoardDetail, columnId: string): BoardDetail {
  return { ...board, columns: board.columns.filter((c) => c.id !== columnId) };
}

export function withColumnsReordered(board: BoardDetail, columnIds: string[]): BoardDetail {
  const byId = new Map(board.columns.map((c) => [c.id, c]));
  const reordered = columnIds
    .map((id, index) => {
      const column = byId.get(id);
      return column ? { ...column, position: index } : undefined;
    })
    .filter((c): c is ColumnWithTasks => Boolean(c));
  return { ...board, columns: reordered };
}

export function withTaskAdded(board: BoardDetail, columnId: string, task: Task): BoardDetail {
  return {
    ...board,
    columns: board.columns.map((c) => (c.id === columnId ? { ...c, tasks: [...c.tasks, task] } : c)),
  };
}

export interface TaskEdits {
  title?: string;
  description?: string;
  priority?: Priority;
  dueDate?: string | null;
}

export function withTaskUpdated(board: BoardDetail, taskId: string, edits: TaskEdits): BoardDetail {
  return {
    ...board,
    columns: board.columns.map((c) => ({
      ...c,
      tasks: c.tasks.map((t) => (t.id === taskId ? { ...t, ...edits, updatedAt: new Date().toISOString() } : t)),
    })),
  };
}

export function withTaskRemoved(board: BoardDetail, taskId: string): BoardDetail {
  return {
    ...board,
    columns: board.columns.map((c) => ({ ...c, tasks: c.tasks.filter((t) => t.id !== taskId) })),
  };
}

/** Moves a task to `columnId` at `position`, reindexing both columns — mirrors api/client.ts#moveTask. */
export function withTaskMoved(
  board: BoardDetail,
  taskId: string,
  columnId: string,
  position: number,
): BoardDetail {
  let moving: Task | undefined;
  const withoutTask = board.columns.map((c) => {
    const found = c.tasks.find((t) => t.id === taskId);
    if (found) moving = found;
    return { ...c, tasks: c.tasks.filter((t) => t.id !== taskId) };
  });
  if (!moving) return board;

  const clamped = Math.max(0, Math.min(position, withoutTask.find((c) => c.id === columnId)?.tasks.length ?? 0));

  return {
    ...board,
    columns: withoutTask.map((c) => {
      if (c.id !== columnId) return { ...c, tasks: c.tasks.map((t, i) => ({ ...t, position: i })) };
      const tasks = [...c.tasks];
      tasks.splice(clamped, 0, { ...(moving as Task), columnId, position: clamped });
      return { ...c, tasks: tasks.map((t, i) => ({ ...t, position: i })) };
    }),
  };
}
