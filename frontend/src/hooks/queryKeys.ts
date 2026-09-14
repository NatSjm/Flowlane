export const queryKeys = {
  boards: ["boards"] as const,
  board: (boardId: string) => ["board", boardId] as const,
};
