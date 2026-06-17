import { useState, useEffect, useRef } from "react";
import { type TaskEvent } from "@/lib/store";
import {
  Check,
  Loader2,
  X,
  ChevronRight,
  Circle,
  Network,
  Wrench,
  Zap,
  Timer,
} from "lucide-react";

const stepMeta: Record<
  string,
  { label: string; group: "orchestrator" | "agents" | "output" | "tool_info" }
> = {
  submitted: { label: "Query submitted", group: "orchestrator" },
  validating_query: { label: "Validating query", group: "orchestrator" },
  discovering_agents: { label: "Discovering agents", group: "orchestrator" },
  routing: { label: "Routing to agents", group: "orchestrator" },
  selecting_agents: { label: "Selecting agents", group: "orchestrator" },
  decomposing_task: { label: "Decomposing task", group: "orchestrator" },
  aggregating: { label: "Aggregating results", group: "output" },
  research_task: { label: "Research Agent", group: "agents" },
  solution_task: { label: "Solution Agent", group: "agents" },
  experiment_task: { label: "Experiment Agent", group: "agents" },
  research: { label: "Research Agent", group: "agents" },
  solution: { label: "Solution Agent", group: "agents" },
  experiment: { label: "Experiment Agent", group: "agents" },
};

const agentColorMap: Record<string, { ring: string; text: string; bg: string; badge: string }> = {
  research: {
    ring: "ring-cyan-500/40",
    text: "text-cyan-400",
    bg: "bg-cyan-500/10",
    badge: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
  },
  solution: {
    ring: "ring-violet-500/40",
    text: "text-violet-400",
    bg: "bg-violet-500/10",
    badge: "border-violet-500/30 bg-violet-500/10 text-violet-300",
  },
  experiment: {
    ring: "ring-amber-500/40",
    text: "text-amber-400",
    bg: "bg-amber-500/10",
    badge: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  },
};

function StatusIcon({ status, size = "sm" }: { status: string; size?: "sm" | "xs" }) {
  const dim = size === "xs" ? "h-2.5 w-2.5" : "h-3 w-3";
  if (status === "running") {
    return <Loader2 className={`${dim} animate-spin text-blue-400`} />;
  }
  if (status === "complete") {
    return <Check className={`${dim} text-green-400`} />;
  }
  if (status === "error") {
    return <X className={`${dim} text-red-400`} />;
  }
  return <Circle className="h-1.5 w-1.5 text-text-muted" />;
}

function parseToolsUsed(events: TaskEvent[], agentName: string): string[] {
  const toolEvent = events.find(
    (ev) => ev.step === agentName && ev.status === "tool_info",
  );
  if (!toolEvent) return [];
  try {
    const parsed = JSON.parse(toolEvent.detail);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function parseRoutingDetail(detail: string): { agents?: string[]; reasoning?: string } | null {
  try {
    const parsed = JSON.parse(detail);
    if (parsed && typeof parsed === "object" && Array.isArray(parsed.agents)) {
      return parsed;
    }
  } catch {}
  return null;
}

function parseRunningTools(detail: string): string[] {
  try {
    const parsed = JSON.parse(detail);
    if (parsed && Array.isArray(parsed.tools)) {
      return parsed.tools.filter((t: unknown) => typeof t === "string");
    }
  } catch {}
  return [];
}

function formatElapsed(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  if (min > 0) return `${min}m ${sec}s`;
  return `${sec}s`;
}

function toMs(ts: number): number {
  return ts < 1e12 ? ts * 1000 : ts;
}

function ElapsedTimer({ events }: { events: TaskEvent[] }) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (events.length === 0) return;

    const firstTs = events.reduce((min, e) => Math.min(min, toMs(e.timestamp)), Infinity);
    startRef.current = firstTs;

    const tick = () => {
      setElapsed(Date.now() - startRef.current);
    };
    tick();
    intervalRef.current = setInterval(tick, 200);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [events]);

  const isRunning = events.some((e) => e.status === "running");
  const isComplete = events.some((e) => e.step === "aggregating" && e.status === "complete");

  useEffect(() => {
    if (isComplete && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [isComplete]);

  if (isComplete) {
    const lastEvent = events.find((e) => e.step === "aggregating" && e.status === "complete");
    if (lastEvent) {
      const totalMs = toMs(lastEvent.timestamp) - startRef.current;
      return (
        <span className="ml-auto flex items-center gap-1 text-[10px] font-mono text-emerald-400">
          <Timer className="h-2.5 w-2.5" />
          {formatElapsed(totalMs)}
        </span>
      );
    }
  }

  if (!isRunning && events.length > 0) {
    return null;
  }

  return (
    <span className="ml-auto flex items-center gap-1 text-[10px] font-mono text-blue-400">
      <Timer className="h-2.5 w-2.5" />
      {formatElapsed(elapsed)}
    </span>
  );
}

function ToolPill({ name, delay }: { name: string; delay: number }) {
  const displayName = name.replace(/_/g, " ");
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-background/80 px-1.5 py-0.5 text-[10px] font-medium text-text-secondary transition-all duration-300 animate-in fade-in slide-in-from-left-1"
      style={{ animationDelay: `${delay}ms` }}
    >
      <Wrench className="h-2.5 w-2.5 text-text-muted" />
      {displayName}
    </span>
  );
}

function deduplicateEvents(events: TaskEvent[]): TaskEvent[] {
  const latest = new Map<string, TaskEvent>();
  for (const ev of events) {
    const existing = latest.get(ev.step);
    if (!existing || ev.timestamp >= existing.timestamp) {
      latest.set(ev.step, ev);
    }
  }
  return Array.from(latest.values());
}

function orderSteps(steps: string[]): string[] {
  const order = [
    "submitted",
    "validating_query",
    "discovering_agents",
    "routing",
    "selecting_agents",
    "decomposing_task",
    "aggregating",
  ];
  return steps.sort((a, b) => {
    const ai = order.indexOf(a);
    const bi = order.indexOf(b);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });
}

function ActiveToolsIndicator({ agentEvents }: { agentEvents: TaskEvent[] }) {
  const activeTools: { agent: string; tool: string }[] = [];
  for (const ev of agentEvents) {
    if (ev.status === "running") {
      const tools = parseRunningTools(ev.detail);
      const agentLabel = stepMeta[ev.step]?.label || ev.step;
      for (const t of tools) {
        activeTools.push({ agent: agentLabel, tool: t });
      }
    }
  }
  if (activeTools.length === 0) return null;
  return (
    <div className="mt-2 flex items-center gap-1.5 rounded-md border border-blue-500/20 bg-blue-500/5 px-2 py-1">
      <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
      <span className="text-[10px] font-medium text-blue-300">
        Invoking:{" "}
        {activeTools.map((at, i) => (
          <span key={at.tool}>
            {i > 0 && " + "}
            <span className="text-blue-200">{at.tool.replace(/_/g, " ")}</span>
            <span className="text-blue-400/60"> on {at.agent}</span>
          </span>
        ))}
      </span>
    </div>
  );
}

export function TaskProgress({ events }: { events: TaskEvent[] }) {
  if (!events || events.length === 0) return null;

  const unique = deduplicateEvents(events);

  const orchestratorSteps = orderSteps(
    unique
      .filter((ev) => {
        const meta = stepMeta[ev.step];
        return meta?.group === "orchestrator" || ev.step === "submitted";
      })
      .map((ev) => ev.step),
  );
  const orchestratorEvents = orchestratorSteps.map(
    (step) => unique.find((ev) => ev.step === step)!,
  );

  const agentSteps = unique
    .filter((ev) => stepMeta[ev.step]?.group === "agents")
    .map((ev) => ev.step);
  const agentEvents = agentSteps.map((step) => unique.find((ev) => ev.step === step)!);

  const outputSteps = unique
    .filter((ev) => stepMeta[ev.step]?.group === "output")
    .map((ev) => ev.step);
  const outputEvents = outputSteps.map((step) => unique.find((ev) => ev.step === step)!);

  const hasAgents = agentEvents.length > 0;
  const activeAgentCount = agentEvents.filter((e) => e.status === "running").length;
  const doneAgentCount = agentEvents.filter((e) => e.status === "complete").length;

  const totalToolsUsed = agentEvents.reduce((acc, ev) => {
    const agentKey = ev.step.replace("_task", "");
    return acc + parseToolsUsed(unique, ev.step).length;
  }, 0);

  return (
    <div className="mb-3 rounded-xl border border-border bg-surface/50 p-3 text-xs">
      <div className="mb-2 flex items-center gap-2 text-[11px] font-medium text-text-muted uppercase tracking-wider">
        <Network className="h-3 w-3" />
        A2A Agent Pipeline
        <ElapsedTimer events={events} />
        {totalToolsUsed > 0 && (
          <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-1.5 py-0 text-emerald-400">
            <Zap className="h-2.5 w-2.5" />
            {totalToolsUsed} MCP tools
          </span>
        )}
      </div>

      <div className="relative">
        <div className="absolute left-[7px] top-0 bottom-0 w-px bg-border" />

        <div className="space-y-0.5">
          {orchestratorEvents.map((ev) => {
            const meta = stepMeta[ev.step];
            const routingInfo = ev.step === "routing" && ev.status === "complete"
              ? parseRoutingDetail(ev.detail)
              : null;
            return (
              <div key={ev.step} className="relative flex items-center gap-2 pl-0">
                <div className="relative z-10 flex h-4 w-4 items-center justify-center rounded-full bg-surface">
                  <StatusIcon status={ev.status} />
                </div>
                <span
                  className={`text-xs ${
                    ev.status === "running"
                      ? "text-foreground"
                      : ev.status === "complete"
                        ? "text-text-secondary"
                        : "text-text-muted"
                  }`}
                >
                  {meta?.label || ev.step}
                </span>
                {ev.status === "running" && (
                  <span className="ml-1 animate-pulse text-[10px] text-text-muted">
                    ...
                  </span>
                )}
                {routingInfo && routingInfo.agents && routingInfo.agents.length > 0 && (
                  <span className="ml-1 text-[10px] text-text-muted">
                    → {routingInfo.agents.join(", ")}
                  </span>
                )}
                {!routingInfo && ev.status === "complete" && ev.detail && ev.step !== "routing" && (
                  <span className="ml-1 text-[10px] text-text-muted truncate max-w-[300px]">
                    {ev.detail.length > 60 ? ev.detail.slice(0, 60) + "..." : ev.detail}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {hasAgents && (
          <div className="relative mt-1 ml-0">
            <div className="absolute left-[7px] top-0 h-2 w-px bg-border" />

            <div className="ml-5 mt-1 rounded-lg border border-border/50 bg-background/50 p-2">
              <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-text-muted">
                <ChevronRight className="h-2.5 w-2.5" />
                Invoking sub-agents over A2A
                {activeAgentCount > 0 && (
                  <span className="rounded-full bg-blue-500/10 px-1.5 py-0 text-blue-400">
                    {activeAgentCount} active
                  </span>
                )}
                {doneAgentCount > 0 && (
                  <span className="rounded-full bg-green-500/10 px-1.5 py-0 text-green-400">
                    {doneAgentCount} done
                  </span>
                )}
              </div>
              <div className="space-y-1">
                {agentEvents.map((ev) => {
                  const meta = stepMeta[ev.step];
                  const agentKey = ev.step.replace("_task", "");
                  const colors = agentColorMap[agentKey] || agentColorMap.research;
                  const tools = parseToolsUsed(unique, ev.step);

                  return (
                    <div key={ev.step} className="group">
                      <div
                        className={`flex items-center gap-2 rounded-md px-1 py-0.5 transition-colors ${
                          ev.status === "running" ? `${colors.bg} ring-1 ${colors.ring}` : ""
                        }`}
                      >
                        <div className="relative z-10 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-surface">
                          <StatusIcon status={ev.status} size="xs" />
                        </div>
                        <span
                          className={`text-xs ${
                            ev.status === "running"
                              ? "text-foreground"
                              : ev.status === "complete"
                                ? "text-text-secondary"
                                : "text-text-muted"
                          }`}
                        >
                          {meta?.label || ev.step}
                        </span>
                        {tools.length > 0 && (
                          <span
                            className={`ml-auto rounded-full px-1.5 py-0 text-[9px] font-medium ${colors.badge}`}
                          >
                            {tools.length} {tools.length === 1 ? "tool" : "tools"}
                          </span>
                        )}
                      </div>

                      {tools.length > 0 && (
                        <div className="ml-4 mt-0.5 flex flex-wrap gap-1 pl-2 border-l border-border/30 py-0.5">
                          {tools.map((tool, i) => (
                            <ToolPill key={tool} name={tool} delay={i * 50} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {outputEvents.length > 0 && (
          <div className="space-y-0.5 mt-1">
            {outputEvents.map((ev) => {
              const meta = stepMeta[ev.step];
              return (
                <div key={ev.step} className="relative flex items-center gap-2 pl-0">
                  <div className="relative z-10 flex h-4 w-4 items-center justify-center rounded-full bg-surface">
                    <StatusIcon status={ev.status} />
                  </div>
                  <span
                    className={`text-xs ${
                      ev.status === "running"
                        ? "text-foreground"
                        : ev.status === "complete"
                          ? "text-text-secondary"
                          : "text-text-muted"
                    }`}
                  >
                    {meta?.label || ev.step}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <ActiveToolsIndicator agentEvents={agentEvents} />
      </div>
    </div>
  );
}
