import { useSortable } from "@dnd-kit/sortable";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ColumnWithTasks, Task } from "../../types";
import { ColumnHeader } from "./ColumnHeader";
import { TaskCard } from "../Task/TaskCard";
import { AddTaskForm } from "../Task/AddTaskForm";

interface ColumnProps {
  column: ColumnWithTasks;
  visibleTasks: Task[];
  totalTaskCount: number;
  isFiltering: boolean;
  dragDisabled: boolean;
  onRename: (name: string) => void;
  onDelete: () => void;
  onAddTask: (title: string) => void;
  isAddingTask: boolean;
  onOpenTask: (task: Task) => void;
}

export function Column({
  column,
  visibleTasks,
  totalTaskCount,
  isFiltering,
  dragDisabled,
  onRename,
  onDelete,
  onAddTask,
  isAddingTask,
  onOpenTask,
}: ColumnProps) {
  const {
    attributes,
    listeners,
    setNodeRef: setSortableRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: column.id, data: { type: "column" }, disabled: dragDisabled });

  const { setNodeRef: setDroppableRef } = useDroppable({
    id: column.id,
    data: { type: "column", columnId: column.id },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setSortableRef}
      style={style}
      {...attributes}
      className={`flex w-72 shrink-0 flex-col rounded-lg bg-slate-100/80 p-2 ${isDragging ? "opacity-50" : ""}`}
    >
      <ColumnHeader
        name={column.name}
        taskCount={visibleTasks.length}
        totalTaskCount={totalTaskCount}
        onRename={onRename}
        onDelete={onDelete}
        dragHandleProps={{ ...listeners }}
      />

      <div
        ref={setDroppableRef}
        className="scrollbar-thin flex min-h-[2.5rem] max-h-[calc(100vh-260px)] flex-col gap-2 overflow-y-auto px-0.5 pb-1"
      >
        <SortableContext items={visibleTasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          {visibleTasks.map((task) => (
            <TaskCard key={task.id} task={task} onOpen={() => onOpenTask(task)} dragDisabled={dragDisabled} />
          ))}
        </SortableContext>

        {visibleTasks.length === 0 && (
          <p className="rounded-md border border-dashed border-slate-300 px-2 py-3 text-center text-xs text-slate-400">
            {isFiltering ? "No tasks match" : "No tasks in this column"}
          </p>
        )}
      </div>

      {!isFiltering && <AddTaskForm onCreate={onAddTask} isPending={isAddingTask} />}
    </div>
  );
}
