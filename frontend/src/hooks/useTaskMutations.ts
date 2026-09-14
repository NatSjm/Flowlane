import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { CreateTaskInput, MoveTaskInput, UpdateTaskInput } from "../api";
import type { BoardDetail } from "../types";
import { queryKeys } from "./queryKeys";
import { withTaskMoved, withTaskRemoved, withTaskUpdated } from "../utils/boardTransforms";

/**
 * Task mutations follow the spec §11 optimistic-update contract: update the
 * cached board immediately, persist via the API, and roll back to
 * the snapshot if the request fails.
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

export function useCreateTaskMutation(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ columnId, input }: { columnId: string; input: CreateTaskInput }) =>
      api.createTask(columnId, input),
    onSuccess: () => {
      // A new task needs a server-issued id, so refetch rather than
      // optimistically guessing one.
      queryClient.invalidateQueries({ queryKey: queryKeys.board(boardId) });
    },
  });
}

export function useUpdateTaskMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: ({ taskId, input }: { taskId: string; input: UpdateTaskInput }) =>
      api.updateTask(taskId, input),
    onMutate: async ({ taskId, input }) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      if (input.columnId) {
        board.apply((b) => withTaskMoved(b, taskId, input.columnId as string, Number.MAX_SAFE_INTEGER));
      }
      board.apply((b) => withTaskUpdated(b, taskId, input));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
    },
    onSettled: () => board.queryClient.invalidateQueries({ queryKey: board.key }),
  });
}

export function useDeleteTaskMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: (taskId: string) => api.deleteTask(taskId),
    onMutate: async (taskId) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      board.apply((b) => withTaskRemoved(b, taskId));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
      board.queryClient.invalidateQueries({ queryKey: board.key });
    },
  });
}

export function useMoveTaskMutation(boardId: string) {
  const board = useOptimisticBoardUpdate(boardId);
  return useMutation({
    mutationFn: ({ taskId, input }: { taskId: string; input: MoveTaskInput }) => api.moveTask(taskId, input),
    onMutate: async ({ taskId, input }) => {
      await board.queryClient.cancelQueries({ queryKey: board.key });
      const previous = board.snapshot();
      board.apply((b) => withTaskMoved(b, taskId, input.columnId, input.position));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      board.rollback(context?.previous);
      board.queryClient.invalidateQueries({ queryKey: board.key });
    },
  });
}
