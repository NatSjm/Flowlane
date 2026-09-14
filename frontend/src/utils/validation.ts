/**
 * Shared validation rules, mirrored from `_docs/specs.md` §13. These run
 * client-side for instant feedback; the server re-checks the same rules
 * (server/src/flowlane_api/schemas/) and returns the same messages.
 */

export const BOARD_NAME_MAX = 100;
export const COLUMN_NAME_MAX = 50;
export const TASK_TITLE_MAX = 200;
export const TASK_DESCRIPTION_MAX = 5000;

export function validateBoardName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) return "Board name is required";
  if (trimmed.length > BOARD_NAME_MAX) {
    return `Board name must be ${BOARD_NAME_MAX} characters or fewer`;
  }
  return null;
}

export function validateColumnName(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed.length === 0) return "Column name is required";
  if (trimmed.length > COLUMN_NAME_MAX) {
    return `Column name must be ${COLUMN_NAME_MAX} characters or fewer`;
  }
  return null;
}

export function validateTaskTitle(title: string): string | null {
  const trimmed = title.trim();
  if (trimmed.length === 0) return "Task title is required";
  if (trimmed.length > TASK_TITLE_MAX) {
    return `Title must be ${TASK_TITLE_MAX} characters or fewer`;
  }
  return null;
}

export function validateTaskDescription(description: string): string | null {
  if (description.length > TASK_DESCRIPTION_MAX) {
    return `Description must be ${TASK_DESCRIPTION_MAX} characters or fewer`;
  }
  return null;
}

export function validateDueDate(dueDate: string | null): string | null {
  if (!dueDate) return null;
  const date = new Date(dueDate);
  if (Number.isNaN(date.getTime())) return "Due date must be a valid date";
  return null;
}
