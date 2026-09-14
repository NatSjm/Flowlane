import { useState, type FormEvent } from "react";
import { COLUMN_NAME_MAX, validateColumnName } from "../../utils/validation";

interface AddColumnFormProps {
  onCreate: (name: string) => void;
  isPending: boolean;
}

export function AddColumnForm({ onCreate, isPending }: AddColumnFormProps) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setEditing(false);
    setName("");
    setError(null);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const message = validateColumnName(name);
    if (message) {
      setError(message);
      return;
    }
    onCreate(name.trim());
    reset();
  }

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="h-fit w-72 shrink-0 rounded-lg border border-dashed border-slate-300 px-3 py-2.5 text-left text-sm font-medium text-slate-500 hover:border-slate-400 hover:bg-white hover:text-slate-700"
      >
        + Add column
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-72 shrink-0 rounded-lg border border-slate-200 bg-white p-3 shadow-sm"
    >
      <input
        autoFocus
        type="text"
        value={name}
        maxLength={COLUMN_NAME_MAX}
        placeholder="Column name"
        onChange={(event) => setName(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Escape") reset();
        }}
        className="w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      <div className="mt-2 flex items-center gap-2">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          Add column
        </button>
        <button type="button" onClick={reset} className="text-xs font-medium text-slate-500 hover:text-slate-700">
          Cancel
        </button>
      </div>
    </form>
  );
}
