import { useState, type FormEvent } from "react";
import { TASK_TITLE_MAX, validateTaskTitle } from "../../utils/validation";

interface AddTaskFormProps {
  onCreate: (title: string) => void;
  isPending: boolean;
}

export function AddTaskForm({ onCreate, isPending }: AddTaskFormProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setEditing(false);
    setTitle("");
    setError(null);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const message = validateTaskTitle(title);
    if (message) {
      setError(message);
      return;
    }
    onCreate(title.trim());
    reset();
  }

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="w-full rounded-md px-2 py-1.5 text-left text-sm font-medium text-slate-500 hover:bg-slate-200/60 hover:text-slate-700"
      >
        + Add task
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-md bg-white p-2 shadow-sm ring-1 ring-slate-200">
      <textarea
        autoFocus
        value={title}
        maxLength={TASK_TITLE_MAX}
        placeholder="Task title"
        rows={2}
        onChange={(event) => setTitle(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Escape") reset();
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSubmit(event);
          }
        }}
        className="w-full resize-none rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      <div className="mt-2 flex items-center gap-2">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          Add task
        </button>
        <button type="button" onClick={reset} className="text-xs font-medium text-slate-500 hover:text-slate-700">
          Cancel
        </button>
      </div>
    </form>
  );
}
