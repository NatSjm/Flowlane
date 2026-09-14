/**
 * Mirrors the error shape from `_docs/specs.md` §14:
 * { "error": { "code": "...", "message": "..." } }
 *
 * Thrown by src/api/client.ts for every failed request: `code`/`message`
 * come from the server's error envelope, or are `NETWORK_ERROR` /
 * `HTTP_ERROR` when there was no usable response at all.
 */
export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

export function toUserMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return "Something went wrong. Please try again.";
  return "Something went wrong. Please try again.";
}
