import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { queryKeys } from "./queryKeys";

export function useBoardQuery(boardId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.board(boardId ?? ""),
    queryFn: () => api.getBoard(boardId as string),
    enabled: Boolean(boardId),
  });
}
