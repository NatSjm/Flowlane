import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { CreateColumnInput, UpdateColumnInput } from "../api";
import type { BoardDetail } from "../types";
import { queryKeys } from "./queryKeys";
import { withColumnRemoved, withColumnRenamed, withColumnsReordered } from "../utils/boardTransforms";

/**
 * Column mutations follow the spec §11 optimistic-update contract: update
 * the cached board immediately, persist via the (mocked) API, and roll back
 * to the snapshot if the request fails.
 */

function useOptimisticBoardUpdate(boardId: string) {
  const queryClient = useQueryClient();
  return {
    key: queryKeys.board(boardId),
    queryClient,
    snapshot: () => queryClient.getQueryData<BoardDetail>(queryKeys.board(boardId)),
    apply: (updater: (board: BoardDetail) => BoardDetail) => {
      queryClient.setQueryData<BoardDetail>(queryKeys.board(boardId), (current) =>
        current ? updater(current) : current,
      );
    },
    rollback: (previous: BoardDetail | undefined) => {
      queryClient.setQueryData(queryKeys.board(boardId), previous);
    },
  };
}

export function useCreateColumnMutation(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateColumnInput) => api.createColumn(boardId, input),
    onSuccess: () => {
      // A new column needs a server-issued id, so refetch rather than
      // optimistically guessing one.
      queryClient.invalidateQueries({ queryKey: queryKeys.board(boardId) });
    },
  });
}

export function useRenameColumnMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: ({ columnId, input }: { columnId: string; input: UpdateColumnInput }) =>
      api.updateColumn(columnId, input),
    onMutate: async ({ columnId, input }) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      board.apply((b) => withColumnRenamed(b, columnId, input.name));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
      board.queryClient.invalidateQueries({ queryKey: board.key });
    },
  });
}

export function useDeleteColumnMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: (columnId: string) => api.deleteColumn(columnId),
    onMutate: async (columnId) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      board.apply((b) => withColumnRemoved(b, columnId));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
      board.queryClient.invalidateQueries({ queryKey: board.key });
    },
  });
}

export function useReorderColumnsMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: (columnIds: string[]) => api.reorderColumns(boardId, columnIds),
    onMutate: async (columnIds) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      board.apply((b) => withColumnsReordered(b, columnIds));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
      board.queryClient.invalidateQueries({ queryKey: board.key });
    },
  });
}
