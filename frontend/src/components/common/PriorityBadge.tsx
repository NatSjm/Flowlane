import type { Priority } from "../../types";

const STYLES: Record<Priority, string> = {
  HIGH: "bg-red-50 text-red-700 ring-red-600/10",
  MEDIUM: "bg-amber-50 text-amber-700 ring-amber-600/10",
  LOW: "bg-slate-100 text-slate-600 ring-slate-500/10",
};

const DOTS: Record<Priority, string> = {
  HIGH: "🔴",
  MEDIUM: "🟡",
  LOW: "🟢",
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[priority]}`}
    >
      <span aria-hidden="true">{DOTS[priority]}</span>
      {priority}
    </span>
  );
}
