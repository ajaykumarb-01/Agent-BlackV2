import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  MessageSquare,
  History,
  Boxes,
  Settings,
  X,
} from "lucide-react";
import { useEffect } from "react";
import { useAppStore } from "@/lib/store";

const items = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/", label: "Chat", icon: MessageSquare },
  { to: "/history", label: "History", icon: History },
  { to: "/agents", label: "Agents", icon: Boxes },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function SideDrawer() {
  const open = useAppStore((s) => s.drawerOpen);
  const setOpen = useAppStore((s) => s.setDrawerOpen);
  const path = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setOpen]);

  return (
    <>
      <div
        onClick={() => setOpen(false)}
        className={`fixed inset-0 z-40 bg-foreground/30 backdrop-blur-sm transition-opacity ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <aside
        className={`fixed left-0 top-0 z-50 h-full w-72 border-r border-border bg-surface transition-transform ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between px-4 border-b border-border">
          <span className="text-sm font-semibold">Navigation</span>
          <button
            onClick={() => setOpen(false)}
            className="rounded-md p-1.5 hover:bg-surface-hover"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <nav className="p-2">
          {items.map(({ to, label, icon: Icon }) => {
            const active = path === to;
            return (
              <Link
                key={to}
                to={to}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? "bg-foreground text-background"
                    : "text-foreground hover:bg-surface-hover"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 text-xs text-text-muted">
          v0.1.0 · monochrome
        </div>
      </aside>
    </>
  );
}
