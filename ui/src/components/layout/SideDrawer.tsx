import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  MessageSquare,
  History,
  Boxes,
  Settings,
  Info,
  X,
  ScrollText,
} from "lucide-react";
import { useEffect, useRef, useCallback } from "react";
import { useAppStore } from "@/lib/store";

const items = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/", label: "Chat", icon: MessageSquare, search: { new: "1" as const } },
  { to: "/history", label: "History", icon: History },
  { to: "/agents", label: "Agents", icon: Boxes },
  { to: "/logs", label: "Logs", icon: ScrollText },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/about", label: "About", icon: Info },
] as const;

export function SideDrawer() {
  const open = useAppStore((s) => s.drawerOpen);
  const setOpen = useAppStore((s) => s.setDrawerOpen);
  const path = useRouterState({ select: (s) => s.location.pathname });
  const touchStartX = useRef(0);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (diff > 80) setOpen(false);
  }, [setOpen]);

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
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
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
          {items.map(({ to, label, icon: Icon, search }) => {
            const active = path === to;
            return (
              <Link
                key={to}
                to={to}
                search={search}
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
        <div className="absolute bottom-4 left-4 right-4">
          <Link
            to="/about"
            onClick={() => setOpen(false)}
            className="block text-xs text-text-muted hover:text-foreground transition-colors"
          >
            Agent Black V2 · Multi-Agent Research Ecosystem
          </Link>
        </div>
      </aside>
    </>
  );
}
