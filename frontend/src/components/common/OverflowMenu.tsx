import { useEffect, useRef, useState, type ReactNode } from "react";

export interface OverflowMenuItem {
  label: string;
  onSelect: () => void;
  danger?: boolean;
}

interface OverflowMenuProps {
  items: OverflowMenuItem[];
  label?: string;
  trigger?: ReactNode;
  align?: "left" | "right";
}

export function OverflowMenu({ items, label = "Open menu", trigger, align = "right" }: OverflowMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((v) => !v);
        }}
        className={
          trigger
            ? "inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-600 shadow-sm hover:bg-slate-50"
            : "rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
        }
      >
        {trigger ?? (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4.5 w-4.5">
            <path d="M10 3a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM10 8.5A1.5 1.5 0 1 1 10 11.5 1.5 1.5 0 0 1 10 8.5ZM10 14A1.5 1.5 0 1 1 10 17 1.5 1.5 0 0 1 10 14Z" />
          </svg>
        )}
      </button>
      {open && (
        <div
          role="menu"
          className={`absolute z-20 mt-1 w-40 overflow-hidden rounded-md bg-white py-1 shadow-lg ring-1 ring-slate-900/10 ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              onClick={(event) => {
                event.stopPropagation();
                setOpen(false);
                item.onSelect();
              }}
              className={`block w-full px-3 py-1.5 text-left text-sm hover:bg-slate-50 ${
                item.danger ? "text-red-600" : "text-slate-700"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
