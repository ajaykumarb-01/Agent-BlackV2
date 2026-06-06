import { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { StatusDot } from "@/components/shared/StatusDot";
import { useAppStore } from "@/lib/store";
import { api, type AgentStats } from "@/lib/api";

const AGENTS = [
  { name: "Research", port: 8001, key: "research-agent" },
  { name: "Solution", port: 8002, key: "solution-agent" },
  { name: "Experiment", port: 8003, key: "experiment-agent" },
];

export function StatusBar() {
  const [open, setOpen] = useState(true);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, string>>({});
  const [stats, setStats] = useState<AgentStats | null>(null);
  const provider = useAppStore((s) => s.provider);

  useEffect(() => {
    const fetch = () => {
      api.status().then((s) => {
        setAgentStatuses(s.agents);
      }).catch(() => {});
      api.agentStats().then(setStats).catch(() => {});
    };
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = Math.floor(s % 60);
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  };

  return (
    <div className="rounded-xl border border-border bg-surface/60">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-2.5"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          {AGENTS.map((a) => (
            <span key={a.name} className="inline-flex items-center gap-1.5 text-xs">
              <StatusDot status={agentStatuses[a.key] === "running" ? "online" : "offline"} />
              <span className="text-foreground font-medium">{a.name}</span>
              <span className="text-text-muted">:{a.port}</span>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs text-text-secondary">
          <span className="hidden sm:inline">Selection: <span className="text-foreground font-medium">auto</span></span>
          <span className="rounded-md border border-border bg-background px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider">
            {provider}
          </span>
          <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "" : "-rotate-90"}`} />
        </div>
      </button>
      {open && (
        <div className="border-t border-border-light px-4 py-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <Stat label="Total Tools" value="39" />
          <Stat
            label="Active Agents"
            value={stats ? `${stats.active_agents} / ${stats.total_agents}` : "—"}
          />
          <Stat label="Uptime" value={stats ? formatUptime(stats.uptime) : "—"} />
          <Stat label="Avg Response" value={stats ? `${stats.avg_response_time.toFixed(1)}s` : "—"} />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-text-muted text-[10px] uppercase tracking-wider">{label}</span>
      <span className="text-foreground font-medium">{value}</span>
    </div>
  );
}
