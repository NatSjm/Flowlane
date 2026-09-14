import { useEffect, useRef, useState } from "react";
import type { Priority } from "../../types";

export type DueFilter = "OVERDUE" | "DUE_TODAY" | "DUE_WEEK";

interface SearchFilterBarProps {
  query: string;
  onQueryChange: (value: string) => void;
  priorities: Set<Priority>;
  onTogglePriority: (priority: Priority) => void;
  due: Set<DueFilter>;
  onToggleDue: (value: DueFilter) => void;
  onClear: () => void;
}

const PRIORITY_OPTIONS: Priority[] = ["LOW", "MEDIUM", "HIGH"];
const DUE_OPTIONS: { value: DueFilter; label: string }[] = [
  { value: "OVERDUE", label: "Overdue" },
  { value: "DUE_TODAY", label: "Due today" },
  { value: "DUE_WEEK", label: "Due this week" },
];

export function SearchFilterBar({
  query,
  onQueryChange,
  priorities,
  onTogglePriority,
  due,
  onToggleDue,
  onClear,
}: SearchFilterBarProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const activeCount = priorities.size + due.size;

  useEffect(() => {
    if (!open) return;
    function handleClick(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
        >
          <path
            fillRule="evenodd"
            d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.452 4.391l3.328 3.329a.75.75 0 1 1-1.06 1.06l-3.329-3.328A7 7 0 0 1 2 9Z"
            clipRule="evenodd"
          />
        </svg>
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search tasks…"
          aria-label="Search tasks"
          className="w-48 rounded-md border border-slate-300 bg-white py-1.5 pl-8 pr-3 text-sm shadow-sm focus:w-64 focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:w-56"
        />
      </div>

      <div className="relative" ref={ref}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium shadow-sm ${
            activeCount > 0
              ? "border-indigo-200 bg-indigo-50 text-indigo-700"
              : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
          }`}
        >
          Filters
          {activeCount > 0 && (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-indigo-600 px-1 text-xs font-semibold text-white">
              {activeCount}
            </span>
          )}
        </button>

        {open && (
          <div className="absolute right-0 z-20 mt-1 w-56 rounded-md bg-white p-3 shadow-lg ring-1 ring-slate-900/10">
            <fieldset>
              <legend className="text-xs font-semibold uppercase tracking-wide text-slate-500">Priority</legend>
              <div className="mt-2 space-y-1.5">
                {PRIORITY_OPTIONS.map((priority) => (
                  <label key={priority} className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={priorities.has(priority)}
                      onChange={() => onTogglePriority(priority)}
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    {priority.charAt(0) + priority.slice(1).toLowerCase()}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="mt-3">
              <legend className="text-xs font-semibold uppercase tracking-wide text-slate-500">Due date</legend>
              <div className="mt-2 space-y-1.5">
                {DUE_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={due.has(option.value)}
                      onChange={() => onToggleDue(option.value)}
                      className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    {option.label}
                  </label>
                ))}
              </div>
            </fieldset>

            {activeCount > 0 && (
              <button
                type="button"
                onClick={onClear}
                className="mt-3 text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
