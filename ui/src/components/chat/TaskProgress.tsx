import { type TaskEvent } from "@/lib/store";
import { Check, Loader2, X, ArrowRight } from "lucide-react";

export function TaskProgress({ events }: { events: TaskEvent[] }) {
  if (!events || events.length === 0) return null;

  return (
    <div className="mb-3 rounded-xl border border-border bg-surface/50 p-3 text-xs">
      <div className="mb-1.5 flex items-center gap-2 text-[11px] font-medium text-text-muted uppercase tracking-wider">
        <Loader2 className="h-3 w-3 animate-spin" />
        Agent progress
      </div>
      <div className="space-y-1">
        {events.map((ev, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="mt-0.5 shrink-0">
              {ev.status === "running" ? (
                <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
              ) : ev.status === "complete" ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : ev.status === "error" ? (
                <X className="h-3 w-3 text-red-500" />
              ) : (
                <ArrowRight className="h-3 w-3 text-text-muted" />
              )}
            </span>
            <span className="text-text-secondary">
              {ev.detail || ev.step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
