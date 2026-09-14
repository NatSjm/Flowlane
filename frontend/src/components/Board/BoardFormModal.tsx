import { useState, type FormEvent } from "react";
import { Modal } from "../common/Modal";
import { BOARD_NAME_MAX, validateBoardName } from "../../utils/validation";

interface BoardFormModalProps {
  title: string;
  submitLabel: string;
  initialName?: string;
  isPending?: boolean;
  onSubmit: (name: string) => void;
  onClose: () => void;
}

export function BoardFormModal({
  title,
  submitLabel,
  initialName = "",
  isPending = false,
  onSubmit,
  onClose,
}: BoardFormModalProps) {
  const [name, setName] = useState(initialName);
  const [touched, setTouched] = useState(false);
  const error = touched ? validateBoardName(name) : null;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (validateBoardName(name)) return;
    onSubmit(name.trim());
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="board-name" className="block text-sm font-medium text-slate-700">
          Board name
        </label>
        <input
          id="board-name"
          type="text"
          autoFocus
          value={name}
          maxLength={BOARD_NAME_MAX}
          onChange={(event) => setName(event.target.value)}
          onBlur={() => setTouched(true)}
          placeholder="e.g. Website Redesign"
          className={`mt-1 w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
            error ? "border-red-300" : "border-slate-300"
          }`}
        />
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {isPending ? "Saving…" : submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
}
