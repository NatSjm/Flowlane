import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Task } from "../../types";
import { PriorityBadge } from "../common/PriorityBadge";
import { formatDueDate, isDueToday, isOverdue } from "../../utils/date";

interface TaskCardProps {
  task: Task;
  onOpen: () => void;
  dragDisabled?: boolean;
}

export function TaskCard({ task, onOpen, dragDisabled = false }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    data: { type: "task", columnId: task.columnId },
    disabled: dragDisabled,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const overdue = isOverdue(task.dueDate);
  const dueToday = isDueToday(task.dueDate);

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter") onOpen();
      }}
      role="button"
      tabIndex={0}
      aria-label={`Open task ${task.title}`}
      className={`cursor-grab touch-none rounded-md bg-white p-3 text-left shadow-sm ring-1 ring-slate-200 transition hover:ring-indigo-300 active:cursor-grabbing ${
        isDragging ? "opacity-40" : ""
      }`}
    >
      <p className="text-sm font-medium text-slate-800">{task.title}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <PriorityBadge priority={task.priority} />
        {task.dueDate && (
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
              overdue
                ? "bg-red-50 text-red-700"
                : dueToday
                  ? "bg-amber-50 text-amber-700"
                  : "bg-slate-50 text-slate-500"
            }`}
          >
            {overdue ? "Overdue: " : ""}
            {formatDueDate(task.dueDate)}
          </span>
        )}
      </div>
    </div>
  );
}
