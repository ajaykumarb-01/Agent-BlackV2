import { useState, useMemo } from "react";
import { ChevronDown, Wifi, WifiOff } from "lucide-react";
import { StatusDot } from "@/components/shared/StatusDot";
import { useAppStore } from "@/lib/store";
import { api, type AgentCard, type AgentStats, type SystemStatus } from "@/lib/api";
import { usePolling } from "@/hooks/use-polling";
import { useLiveUptime } from "@/hooks/use-live-uptime";

const AGENTS = [
  { name: "Research", port: 8001, key: "research-agent", color: "text-blue-400" },
  { name: "Solution", port: 8002, key: "solution-agent", color: "text-emerald-400" },
  { name: "Experiment", port: 8003, key: "experiment-agent", color: "text-purple-400" },
];

export function StatusBar() {
  const [open, setOpen] = useState(true);
  const provider = useAppStore((s) => s.provider);

  const statusPoll = usePolling<SystemStatus>(() => api.status(), { interval: 15000 });
  const statsPoll = usePolling<AgentStats>(() => api.agentStats(), { interval: 15000 });
  const cardPoll = usePolling<{ agents: Record<string, AgentCard | { error: string }> }>(
    () => api.discoverAgents(),
    {
      interval: 30000,
    },
  );

  const status = statusPoll.data;
  const stats = statsPoll.data;
  const uptime = useLiveUptime(stats?.uptime ?? null);
  const cards = useMemo(
    () => Object.values(cardPoll.data?.agents || {}) as Array<AgentCard | { error: string }>,
    [cardPoll.data],
  );
  const cardCount = useMemo(
    () => cards.filter((card) => card?.supportedInterfaces?.length > 0).length,
    [cards],
  );

  const onlineCount = AGENTS.filter((a) => status?.agents?.[a.key] === "running").length;

  return (
    <div className="rounded-xl border border-border bg-surface/60 backdrop-blur-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 hover:bg-surface-hover/30 transition-colors"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          {AGENTS.map((a) => {
            const isOnline = status?.agents?.[a.key] === "running";
            return (
              <span key={a.name} className="inline-flex items-center gap-1.5 text-xs">
                <StatusDot status={isOnline ? "online" : "offline"} />
                <span className={`font-medium ${isOnline ? "text-foreground" : "text-text-muted"}`}>
                  {a.name}
                </span>
                <span className="hidden text-text-muted sm:inline">:{a.port}</span>
              </span>
            );
          })}
        </div>
        <div className="flex items-center gap-2.5 text-xs text-text-secondary">
          <span className={`hidden sm:inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
            onlineCount === AGENTS.length ? "text-emerald-400 border-emerald-500/30" : "text-text-muted"
          }`}>
            {onlineCount === AGENTS.length ? (
              <Wifi className="h-2.5 w-2.5" />
            ) : (
              <WifiOff className="h-2.5 w-2.5" />
            )}
            {onlineCount}/{AGENTS.length}
          </span>
          <span className="hidden rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider sm:inline">
            A2A JSON-RPC
          </span>
          <span className="hidden rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider sm:inline">
            {cardCount}/3 cards
          </span>
          <span className="rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider tabular-nums">
            {provider}
          </span>
          <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-200 ${open ? "" : "-rotate-90"}`} />
        </div>
      </button>
      {open && (
        <div className="border-t border-border-light px-4 py-3 grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
          <Stat label="Protocol" value="A2A" />
          <Stat label="Card Discovery" value={cardPoll.loading ? "checking" : `${cardCount}/3`} />
          <Stat
            label="Active Agents"
            value={stats ? `${stats.active_agents} / ${stats.total_agents}` : "—"}
            highlight={stats?.active_agents === stats?.total_agents}
          />
          <Stat label="Uptime" value={uptime} />
          <Stat
            label="Avg Response"
            value={
              stats?.avg_response_time != null ? `${stats.avg_response_time.toFixed(1)}s` : "—"
            }
          />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className="text-text-muted text-[10px] uppercase tracking-wider">{label}</span>
      <span className={`font-medium tabular-nums ${highlight ? "text-emerald-400" : "text-foreground"}`}>{value}</span>
    </div>
  );
}
