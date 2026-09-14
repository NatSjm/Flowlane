import { useState, type KeyboardEvent } from "react";
import { OverflowMenu } from "../common/OverflowMenu";
import { validateColumnName } from "../../utils/validation";

interface ColumnHeaderProps {
  name: string;
  taskCount: number;
  totalTaskCount: number;
  onRename: (name: string) => void;
  onDelete: () => void;
  dragHandleProps: Record<string, unknown>;
}

export function ColumnHeader({
  name,
  taskCount,
  totalTaskCount,
  onRename,
  onDelete,
  dragHandleProps,
}: ColumnHeaderProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(name);
  const [error, setError] = useState<string | null>(null);

  function commit() {
    const message = validateColumnName(draft);
    if (message) {
      setError(message);
      return;
    }
    if (draft.trim() !== name) onRename(draft.trim());
    setEditing(false);
    setError(null);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") commit();
    if (event.key === "Escape") {
      setDraft(name);
      setEditing(false);
      setError(null);
    }
  }

  return (
    <div className="flex items-start justify-between gap-2 px-1 pb-2" {...dragHandleProps}>
      <div className="min-w-0 flex-1">
        {editing ? (
          <input
            autoFocus
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onBlur={commit}
            onKeyDown={handleKeyDown}
            onPointerDown={(event) => event.stopPropagation()}
            className="w-full rounded-md border border-indigo-300 px-1.5 py-0.5 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        ) : (
          <button
            type="button"
            onDoubleClick={() => setEditing(true)}
            onPointerDown={(event) => event.stopPropagation()}
            className="truncate text-left text-sm font-semibold uppercase tracking-wide text-slate-600"
            title="Double-click to rename"
          >
            {name}
          </button>
        )}
        {error && <p className="mt-0.5 text-xs text-red-600">{error}</p>}
        <p className="mt-0.5 text-xs text-slate-400">
          {totalTaskCount === taskCount ? taskCount : `${taskCount} of ${totalTaskCount}`}
        </p>
      </div>
      <div onPointerDown={(event) => event.stopPropagation()}>
        <OverflowMenu
          label={`Options for ${name} column`}
          items={[
            { label: "Rename", onSelect: () => setEditing(true) },
            { label: "Delete", onSelect: onDelete, danger: true },
          ]}
        />
      </div>
    </div>
  );
}
