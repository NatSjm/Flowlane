import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { CreateBoardInput, UpdateBoardInput } from "../api";
import { queryKeys } from "./queryKeys";

export function useBoardsQuery() {
  return useQuery({
    queryKey: queryKeys.boards,
    queryFn: api.listBoards,
  });
}

export function useCreateBoardMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateBoardInput) => api.createBoard(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.boards });
    },
  });
}

export function useRenameBoardMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ boardId, input }: { boardId: string; input: UpdateBoardInput }) =>
      api.updateBoard(boardId, input),
    onSuccess: (_data, { boardId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.boards });
      queryClient.invalidateQueries({ queryKey: queryKeys.board(boardId) });
    },
  });
}

export function useDeleteBoardMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (boardId: string) => api.deleteBoard(boardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.boards });
    },
  });
}
