import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { SortableContext, arrayMove, horizontalListSortingStrategy, sortableKeyboardCoordinates } from "@dnd-kit/sortable";

import { useBoardQuery } from "../../hooks/useBoard";
import { useDeleteBoardMutation, useRenameBoardMutation } from "../../hooks/useBoards";
import {
  useCreateColumnMutation,
  useDeleteColumnMutation,
  useRenameColumnMutation,
  useReorderColumnsMutation,
} from "../../hooks/useColumnMutations";
import {
  useCreateTaskMutation,
  useDeleteTaskMutation,
  useMoveTaskMutation,
  useUpdateTaskMutation,
} from "../../hooks/useTaskMutations";

import { Column } from "../../components/Column/Column";
import { AddColumnForm } from "../../components/Column/AddColumnForm";
import { TaskCard } from "../../components/Task/TaskCard";
import { TaskModal } from "../../components/Task/TaskModal";
import { BoardFormModal } from "../../components/Board/BoardFormModal";
import { SearchFilterBar, type DueFilter } from "../../components/Board/SearchFilterBar";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { OverflowMenu } from "../../components/common/OverflowMenu";
import { Spinner } from "../../components/common/Spinner";
import { ErrorState } from "../../components/common/ErrorState";
import { EmptyState } from "../../components/common/EmptyState";
import { useToast } from "../../components/common/ToastProvider";
import { toUserMessage } from "../../api";
import type { Column as ColumnType, Priority, Task } from "../../types";
import { isDueThisWeek, isDueToday, isOverdue } from "../../utils/date";

type BoardDialog =
  | { type: "renameBoard" }
  | { type: "deleteBoard" }
  | { type: "deleteColumn"; column: ColumnType }
  | null;

export function BoardPage() {
  const { boardId = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const { data: board, isPending, isError, error, refetch } = useBoardQuery(boardId);

  const renameBoard = useRenameBoardMutation();
  const deleteBoard = useDeleteBoardMutation();
  const createColumn = useCreateColumnMutation(boardId);
  const renameColumn = useRenameColumnMutation(boardId);
  const deleteColumn = useDeleteColumnMutation(boardId);
  const reorderColumns = useReorderColumnsMutation(boardId);
  const createTask = useCreateTaskMutation(boardId);
  const updateTask = useUpdateTaskMutation(boardId);
  const deleteTask = useDeleteTaskMutation(boardId);
  const moveTask = useMoveTaskMutation(boardId);

  const [dialog, setDialog] = useState<BoardDialog>(null);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [activeColumn, setActiveColumn] = useState<ColumnType | null>(null);

  const [query, setQuery] = useState("");
  const [priorities, setPriorities] = useState<Set<Priority>>(new Set());
  const [due, setDue] = useState<Set<DueFilter>>(new Set());

  const isFiltering = query.trim() !== "" || priorities.size > 0 || due.size > 0;

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  function matchesFilters(task: Task): boolean {
    if (query.trim()) {
      const needle = query.trim().toLowerCase();
      const haystack = `${task.title} ${task.description}`.toLowerCase();
      if (!haystack.includes(needle)) return false;
    }
    if (priorities.size > 0 && !priorities.has(task.priority)) return false;
    if (due.size > 0) {
      const matchesDue =
        (due.has("OVERDUE") && isOverdue(task.dueDate)) ||
        (due.has("DUE_TODAY") && isDueToday(task.dueDate)) ||
        (due.has("DUE_WEEK") && isDueThisWeek(task.dueDate));
      if (!matchesDue) return false;
    }
    return true;
  }

  const columns = useMemo(() => board?.columns ?? [], [board]);

  function togglePriority(priority: Priority) {
    setPriorities((current) => {
      const next = new Set(current);
      if (next.has(priority)) next.delete(priority);
      else next.add(priority);
      return next;
    });
  }

  function toggleDue(value: DueFilter) {
    setDue((current) => {
      const next = new Set(current);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  function handleDragStart(event: DragStartEvent) {
    const type = event.active.data.current?.type;
    if (type === "task") {
      const task = columns.flatMap((c) => c.tasks).find((t) => t.id === event.active.id) ?? null;
      setActiveTask(task);
    } else if (type === "column") {
      const column = columns.find((c) => c.id === event.active.id) ?? null;
      setActiveColumn(column);
    }
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveTask(null);
    setActiveColumn(null);
    if (!over) return;

    const activeType = active.data.current?.type;

    if (activeType === "column") {
      if (active.id === over.id) return;
      const oldIndex = columns.findIndex((c) => c.id === active.id);
      const newIndex = columns.findIndex((c) => c.id === over.id);
      if (oldIndex === -1 || newIndex === -1) return;
      const newOrder = arrayMove(columns, oldIndex, newIndex).map((c) => c.id);
      reorderColumns.mutate(newOrder, {
        onError: (err) => toast.showError(toUserMessage(err)),
      });
      return;
    }

    if (activeType === "task") {
      const taskId = String(active.id);
      const overType = over.data.current?.type;
      const overColumnId = (over.data.current?.columnId as string | undefined) ?? String(over.id);
      const destinationColumn = columns.find((c) => c.id === overColumnId);
      if (!destinationColumn) return;

      let position: number;
      if (overType === "task") {
        position = destinationColumn.tasks.findIndex((t) => t.id === over.id);
        if (position === -1) position = destinationColumn.tasks.length;
      } else {
        position = destinationColumn.tasks.length;
      }

      const currentTask = columns.flatMap((c) => c.tasks).find((t) => t.id === taskId);
      if (currentTask && currentTask.columnId === overColumnId && currentTask.position === position) return;

      moveTask.mutate(
        { taskId, input: { columnId: overColumnId, position } },
        { onError: (err) => toast.showError(toUserMessage(err)) },
      );
    }
  }

  if (isPending) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <Spinner label="Loading board…" />
      </div>
    );
  }

  if (isError || !board) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <ErrorState message={toUserMessage(error) || "Board not found"} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <Link to="/" className="shrink-0 text-sm font-medium text-slate-400 hover:text-slate-600">
              ← Boards
            </Link>
            <h1 className="truncate text-lg font-semibold text-slate-900">{board.name}</h1>
          </div>
          <div className="flex items-center gap-2">
            <SearchFilterBar
              query={query}
              onQueryChange={setQuery}
              priorities={priorities}
              onTogglePriority={togglePriority}
              due={due}
              onToggleDue={toggleDue}
              onClear={() => {
                setPriorities(new Set());
                setDue(new Set());
              }}
            />
            <OverflowMenu
              label="Board settings"
              trigger="⚙ Settings"
              items={[
                { label: "Rename board", onSelect: () => setDialog({ type: "renameBoard" }) },
                { label: "Delete board", onSelect: () => setDialog({ type: "deleteBoard" }), danger: true },
              ]}
            />
          </div>
        </div>
        {isFiltering && (
          <p className="mt-2 text-xs text-slate-500">
            Showing filtered results — drag and drop is disabled while a search or filter is active.{" "}
            <button
              type="button"
              className="font-medium text-indigo-600 hover:text-indigo-800"
              onClick={() => {
                setQuery("");
                setPriorities(new Set());
                setDue(new Set());
              }}
            >
              Clear
            </button>
          </p>
        )}
      </header>

      <div className="flex-1 bg-slate-50">
        {columns.length === 0 ? (
          <div className="mx-auto max-w-md px-4 py-10">
            <EmptyState
              title="No columns yet"
              description="Add a column like Todo, In Progress, or Done to start organizing tasks."
            />
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="scrollbar-thin flex items-start gap-3 overflow-x-auto px-4 py-4 sm:px-6">
              <SortableContext items={columns.map((c) => c.id)} strategy={horizontalListSortingStrategy}>
                {columns.map((column) => {
                  const visibleTasks = column.tasks.filter(matchesFilters);
                  return (
                    <Column
                      key={column.id}
                      column={column}
                      visibleTasks={visibleTasks}
                      totalTaskCount={column.tasks.length}
                      isFiltering={isFiltering}
                      dragDisabled={isFiltering}
                      onRename={(name) =>
                        renameColumn.mutate(
                          { columnId: column.id, input: { name } },
                          { onError: (err) => toast.showError(toUserMessage(err)) },
                        )
                      }
                      onDelete={() => setDialog({ type: "deleteColumn", column })}
                      onAddTask={(title) =>
                        createTask.mutate(
                          { columnId: column.id, input: { title } },
                          { onError: (err) => toast.showError(toUserMessage(err)) },
                        )
                      }
                      isAddingTask={createTask.isPending}
                      onOpenTask={setEditingTask}
                    />
                  );
                })}
              </SortableContext>

              <AddColumnForm
                isPending={createColumn.isPending}
                onCreate={(name) =>
                  createColumn.mutate({ name }, { onError: (err) => toast.showError(toUserMessage(err)) })
                }
              />
            </div>

            <DragOverlay>
              {activeTask && <TaskCard task={activeTask} onOpen={() => {}} />}
              {activeColumn && (
                <div className="w-72 rounded-lg bg-slate-100 p-2 shadow-lg ring-1 ring-slate-300">
                  <p className="px-1 text-sm font-semibold uppercase tracking-wide text-slate-600">
                    {activeColumn.name}
                  </p>
                </div>
              )}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {editingTask && (
        <TaskModal
          task={editingTask}
          columns={columns.map((c) => ({ id: c.id, name: c.name }))}
          isSaving={updateTask.isPending}
          isDeleting={deleteTask.isPending}
          onClose={() => setEditingTask(null)}
          onSave={(input) => {
            updateTask.mutate(
              { taskId: editingTask.id, input },
              {
                onSuccess: () => setEditingTask(null),
                onError: (err) => toast.showError(toUserMessage(err)),
              },
            );
          }}
          onDelete={() => {
            deleteTask.mutate(editingTask.id, {
              onSuccess: () => setEditingTask(null),
              onError: (err) => toast.showError(toUserMessage(err)),
            });
          }}
        />
      )}

      {dialog?.type === "renameBoard" && (
        <BoardFormModal
          title="Board settings"
          submitLabel="Save"
          initialName={board.name}
          isPending={renameBoard.isPending}
          onClose={() => setDialog(null)}
          onSubmit={(name) => {
            renameBoard.mutate(
              { boardId, input: { name } },
              {
                onSuccess: () => setDialog(null),
                onError: (err) => toast.showError(toUserMessage(err)),
              },
            );
          }}
        />
      )}

      {dialog?.type === "deleteColumn" && (
        <ConfirmDialog
          title="Delete column"
          message={`Delete "${dialog.column.name}"? Its tasks will be deleted too. This can't be undone.`}
          confirmLabel="Delete column"
          isPending={deleteColumn.isPending}
          onCancel={() => setDialog(null)}
          onConfirm={() => {
            deleteColumn.mutate(dialog.column.id, {
              onSuccess: () => setDialog(null),
              onError: (err) => toast.showError(toUserMessage(err)),
            });
          }}
        />
      )}

      {dialog?.type === "deleteBoard" && (
        <ConfirmDialog
          title="Delete board"
          message={`Delete "${board.name}"? This removes all of its columns and tasks. This can't be undone.`}
          confirmLabel="Delete board"
          isPending={deleteBoard.isPending}
          onCancel={() => setDialog(null)}
          onConfirm={() => {
            deleteBoard.mutate(boardId, {
              onSuccess: () => navigate("/"),
              onError: (err) => toast.showError(toUserMessage(err)),
            });
          }}
        />
      )}
    </div>
  );
}
