/** Date helpers for due-date display and filtering (spec §12). */

export function formatDueDate(dueDate: string | null): string {
  if (!dueDate) return "";
  const date = new Date(dueDate);
  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function startOfDay(date: Date): Date {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

export function isOverdue(dueDate: string | null): boolean {
  if (!dueDate) return false;
  return startOfDay(new Date(dueDate)) < startOfDay(new Date());
}

export function isDueToday(dueDate: string | null): boolean {
  if (!dueDate) return false;
  return startOfDay(new Date(dueDate)).getTime() === startOfDay(new Date()).getTime();
}

export function isDueThisWeek(dueDate: string | null): boolean {
  if (!dueDate) return false;
  const today = startOfDay(new Date());
  const target = startOfDay(new Date(dueDate));
  const diffDays = (target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays < 7;
}

/** Converts a Date (or null) to the yyyy-MM-dd string an <input type="date"> expects. */
export function toDateInputValue(dueDate: string | null): string {
  if (!dueDate) return "";
  const date = new Date(dueDate);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
