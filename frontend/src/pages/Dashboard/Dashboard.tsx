import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useBoardsQuery, useCreateBoardMutation, useDeleteBoardMutation, useRenameBoardMutation } from "../../hooks/useBoards";
import { BoardCard } from "../../components/Board/BoardCard";
import { BoardFormModal } from "../../components/Board/BoardFormModal";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { Spinner } from "../../components/common/Spinner";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { useToast } from "../../components/common/ToastProvider";
import { toUserMessage } from "../../api";
import type { BoardSummary } from "../../types";

type DialogState =
  | { type: "create" }
  | { type: "rename"; board: BoardSummary }
  | { type: "delete"; board: BoardSummary }
  | null;

export function Dashboard() {
  const navigate = useNavigate();
  const toast = useToast();
  const { data: boards, isPending, isError, error, refetch } = useBoardsQuery();
  const createBoard = useCreateBoardMutation();
  const renameBoard = useRenameBoardMutation();
  const deleteBoard = useDeleteBoardMutation();
  const [dialog, setDialog] = useState<DialogState>(null);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">My Boards</h1>
        <button
          type="button"
          onClick={() => setDialog({ type: "create" })}
          className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
        >
          + Create Board
        </button>
      </div>

      <div className="mt-6">
        {isPending && <Spinner label="Loading boards…" />}

        {isError && <ErrorState message={toUserMessage(error)} onRetry={() => refetch()} />}

        {!isPending && !isError && boards && boards.length === 0 && (
          <EmptyState
            title="No boards yet"
            description="Create your first board to start organizing tasks into Todo, In Progress, and Done."
            action={
              <button
                type="button"
                onClick={() => setDialog({ type: "create" })}
                className="mt-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
              >
                + Create Board
              </button>
            }
          />
        )}

        {!isPending && !isError && boards && boards.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {boards.map((board) => (
              <BoardCard
                key={board.id}
                board={board}
                onOpen={() => navigate(`/boards/${board.id}`)}
                onRename={() => setDialog({ type: "rename", board })}
                onDelete={() => setDialog({ type: "delete", board })}
              />
            ))}
          </div>
        )}
      </div>

      {dialog?.type === "create" && (
        <BoardFormModal
          title="Create board"
          submitLabel="Create"
          isPending={createBoard.isPending}
          onClose={() => setDialog(null)}
          onSubmit={(name) => {
            createBoard.mutate(
              { name },
              {
                onSuccess: (board) => {
                  setDialog(null);
                  navigate(`/boards/${board.id}`);
                },
                onError: (err) => toast.showError(toUserMessage(err)),
              },
            );
          }}
        />
      )}

      {dialog?.type === "rename" && (
        <BoardFormModal
          title="Rename board"
          submitLabel="Save"
          initialName={dialog.board.name}
          isPending={renameBoard.isPending}
          onClose={() => setDialog(null)}
          onSubmit={(name) => {
            renameBoard.mutate(
              { boardId: dialog.board.id, input: { name } },
              {
                onSuccess: () => setDialog(null),
                onError: (err) => toast.showError(toUserMessage(err)),
              },
            );
          }}
        />
      )}

      {dialog?.type === "delete" && (
        <ConfirmDialog
          title="Delete board"
          message={`Delete "${dialog.board.name}"? This removes all of its columns and tasks. This can't be undone.`}
          confirmLabel="Delete board"
          isPending={deleteBoard.isPending}
          onCancel={() => setDialog(null)}
          onConfirm={() => {
            deleteBoard.mutate(dialog.board.id, {
              onSuccess: () => setDialog(null),
              onError: (err) => toast.showError(toUserMessage(err)),
            });
          }}
        />
      )}
    </div>
  );
}
