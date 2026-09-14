import { useState } from "react";
import { Modal } from "../common/Modal";
import { ConfirmDialog } from "../common/ConfirmDialog";
import type { Priority, Task } from "../../types";
import { PRIORITIES } from "../../types";
import {
  TASK_DESCRIPTION_MAX,
  TASK_TITLE_MAX,
  validateTaskDescription,
  validateTaskTitle,
} from "../../utils/validation";
import { toDateInputValue } from "../../utils/date";
import type { UpdateTaskInput } from "../../api";

interface TaskModalProps {
  task: Task;
  columns: { id: string; name: string }[];
  isSaving: boolean;
  isDeleting: boolean;
  onSave: (input: UpdateTaskInput) => void;
  onDelete: () => void;
  onClose: () => void;
}

export function TaskModal({ task, columns, isSaving, isDeleting, onSave, onDelete, onClose }: TaskModalProps) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description);
  const [priority, setPriority] = useState<Priority>(task.priority);
  const [dueDate, setDueDate] = useState(toDateInputValue(task.dueDate));
  const [columnId, setColumnId] = useState(task.columnId);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [titleTouched, setTitleTouched] = useState(false);

  const titleError = titleTouched ? validateTaskTitle(title) : null;
  const descriptionError = validateTaskDescription(description);

  function handleSave() {
    setTitleTouched(true);
    if (validateTaskTitle(title) || descriptionError) return;

    const input: UpdateTaskInput = {
      title: title.trim(),
      description: description.trim(),
      priority,
      dueDate: dueDate ? new Date(dueDate).toISOString() : null,
    };
    if (columnId !== task.columnId) input.columnId = columnId;
    onSave(input);
  }

  return (
    <>
      <Modal title="Edit Task" onClose={onClose} widthClassName="max-w-lg">
        <div className="space-y-4">
          <div>
            <label htmlFor="task-title" className="block text-sm font-medium text-slate-700">
              Title
            </label>
            <input
              id="task-title"
              autoFocus
              type="text"
              value={title}
              maxLength={TASK_TITLE_MAX}
              onChange={(event) => setTitle(event.target.value)}
              onBlur={() => setTitleTouched(true)}
              className={`mt-1 w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                titleError ? "border-red-300" : "border-slate-300"
              }`}
            />
            {titleError && <p className="mt-1 text-xs text-red-600">{titleError}</p>}
          </div>

          <div>
            <label htmlFor="task-description" className="block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="task-description"
              rows={4}
              value={description}
              maxLength={TASK_DESCRIPTION_MAX}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Add more detail…"
              className="mt-1 w-full resize-none rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <p className="mt-1 text-right text-xs text-slate-400">
              {description.length}/{TASK_DESCRIPTION_MAX}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="task-priority" className="block text-sm font-medium text-slate-700">
                Priority
              </label>
              <select
                id="task-priority"
                value={priority}
                onChange={(event) => setPriority(event.target.value as Priority)}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p.charAt(0) + p.slice(1).toLowerCase()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="task-due-date" className="block text-sm font-medium text-slate-700">
                Due date
              </label>
              <input
                id="task-due-date"
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              {dueDate && (
                <button
                  type="button"
                  onClick={() => setDueDate("")}
                  className="mt-1 text-xs font-medium text-slate-500 hover:text-slate-700"
                >
                  Clear date
                </button>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="task-column" className="block text-sm font-medium text-slate-700">
              Column
            </label>
            <select
              id="task-column"
              value={columnId}
              onChange={(event) => setColumnId(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {columns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
          >
            Delete
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {isSaving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </Modal>

      {confirmingDelete && (
        <ConfirmDialog
          title="Delete task"
          message={`Delete "${task.title}"? This can't be undone.`}
          confirmLabel="Delete task"
          isPending={isDeleting}
          onCancel={() => setConfirmingDelete(false)}
          onConfirm={onDelete}
        />
      )}
    </>
  );
}
