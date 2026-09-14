/**
 * Mirrors the error shape from `_docs/specs.md` §14:
 * { "error": { "code": "...", "message": "..." } }
 *
 * Thrown by the mock backend (src/api/client.ts) so calling code — and the
 * UI's error states — behave the same way they will once a real HTTP API
 * replaces the mock.
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
