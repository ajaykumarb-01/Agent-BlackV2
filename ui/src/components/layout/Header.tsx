import { Link } from "@tanstack/react-router";
import { Menu, Moon, Sun } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { useDarkMode } from "@/hooks/use-dark-mode";
import { StatusDot } from "@/components/shared/StatusDot";

export function Header() {
  const setDrawerOpen = useAppStore((s) => s.setDrawerOpen);
  const { isDark, toggle } = useDarkMode();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="flex h-14 items-center gap-3 px-4">
        <button
          onClick={() => setDrawerOpen(true)}
          className="rounded-md p-2 text-foreground hover:bg-surface-hover transition-colors"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <Link to="/" className="flex items-center gap-2 group">
          <div className="h-6 w-6 rounded-md bg-foreground flex items-center justify-center">
            <span className="text-[10px] font-bold text-background tracking-tighter">A·B</span>
          </div>
          <span className="text-sm font-semibold tracking-tight">
            Agent Black
          </span>
        </Link>

        <div className="ml-3 hidden sm:flex items-center gap-2 text-xs text-text-secondary">
          <StatusDot status="online" />
          <span>online</span>
        </div>

        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={toggle}
            className="rounded-md p-2 text-foreground hover:bg-surface-hover transition-colors"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </header>
  );
}
