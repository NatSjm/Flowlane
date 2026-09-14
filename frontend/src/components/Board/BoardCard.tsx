import type { BoardSummary } from "../../types";
import { OverflowMenu } from "../common/OverflowMenu";

interface BoardCardProps {
  board: BoardSummary;
  onOpen: () => void;
  onRename: () => void;
  onDelete: () => void;
}

export function BoardCard({ board, onOpen, onRename, onDelete }: BoardCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") onOpen();
      }}
      className="group flex cursor-pointer flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">{board.name}</h3>
        <OverflowMenu
          label={`Options for ${board.name}`}
          items={[
            { label: "Rename", onSelect: onRename },
            { label: "Delete", onSelect: onDelete, danger: true },
          ]}
        />
      </div>
      <p className="mt-3 text-xs text-slate-500">
        {board.columnCount} {board.columnCount === 1 ? "column" : "columns"} · {board.taskCount}{" "}
        {board.taskCount === 1 ? "task" : "tasks"}
      </p>
    </div>
  );
}
