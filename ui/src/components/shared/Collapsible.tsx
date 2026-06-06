import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";

export function Collapsible({
  title,
  defaultOpen = false,
  badge,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  badge?: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border border-border bg-background">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left text-sm font-medium hover:bg-surface-hover/60 rounded-lg transition-colors"
      >
        <span className="flex items-center gap-2">
          <ChevronDown
            className={`h-4 w-4 text-text-secondary transition-transform ${open ? "" : "-rotate-90"}`}
          />
          {title}
          {badge && (
            <span className="text-[10px] uppercase tracking-wider text-text-muted">
              {badge}
            </span>
          )}
        </span>
      </button>
      {open && (
        <div className="border-t border-border-light px-4 py-3">{children}</div>
      )}
    </div>
  );
}
