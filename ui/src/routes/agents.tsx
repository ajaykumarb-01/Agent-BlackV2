import { createFileRoute } from "@tanstack/react-router";
import { StatusDot } from "@/components/shared/StatusDot";
import { Collapsible } from "@/components/shared/Collapsible";
import { useEffect, useState } from "react";
import { api, type DiscoAgent } from "@/lib/api";

export const Route = createFileRoute("/agents")({
  head: () => ({ meta: [      { title: "Agents · Agent Black" }] }),
  component: AgentsPage,
});

const DEFAULT_TOOLS: Record<string, string[]> = {
  "research-agent": [
    "search_papers", "summarize_paper", "analyze_gaps", "find_cv_datasets",
    "recommend_cv_models", "citation_generator", "benchmark_search",
    "eval_metric_advisor", "architecture_comparison", "synthetic_data_strategy",
    "solution_recommendation", "prototype_guidance", "experiment_planner",
  ],
  "solution-agent": [
    "search_papers", "summarize_paper", "find_nlp_datasets", "rag_design",
    "llm_benchmark", "citation_generator", "prompt_optimizer",
    "information_extraction", "eval_metric_advisor", "analyze_gaps",
    "solution_recommendation", "prototype_guidance", "experiment_planner",
  ],
  "experiment-agent": [
    "search_papers", "plan_experiment", "eval_metric_advisor", "hyperparameter_advice",
    "recommend_models", "benchmark_search", "feature_engineering_advisor",
    "model_explainability_advisor", "time_series_strategy", "analyze_gaps",
    "solution_recommendation", "prototype_guidance", "summarize_paper",
  ],
};

function AgentsPage() {
  const [agents, setAgents] = useState<DiscoAgent[]>([]);
  const [logs, setLogs] = useState<Record<string, { stdout: string; stderr: string }>>({});
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    api.getDiscoveredAgents().then((res) => {
      const list = res.agents.map((a) => ({
        ...a,
        tools: DEFAULT_TOOLS[a.name] || [],
      }));
      setAgents(list as any);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async (name: string) => {
    try {
      const data = await api.getAgentLogs(name);
      setLogs((prev) => ({ ...prev, [name]: data }));
    } catch {}
  };

  return (
    <div className="mx-auto w-full max-w-[1100px] px-4 py-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Agents</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => api.startAgents()}
            className="rounded-lg border border-border px-3 py-1.5 text-xs hover:bg-surface-hover"
          >
            Start All
          </button>
          <button
            onClick={() => api.stopAgents()}
            className="rounded-lg border border-border px-3 py-1.5 text-xs hover:bg-surface-hover"
          >
            Stop All
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-sm text-text-muted">
          Loading agents...
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((a: any) => (
            <div key={a.name} className="rounded-xl border border-border bg-surface p-4 flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <StatusDot status={a.status === "running" ? "online" : "offline"} />
                    <h3 className="text-sm font-semibold">{a.name}</h3>
                  </div>
                  <p className="mt-0.5 text-xs text-text-muted font-mono">
                    :{a.port} · {a.last_seen ? new Date(a.last_seen * 1000).toLocaleTimeString() : "unknown"}
                  </p>
                </div>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                {a.capabilities?.join(", ") || "No capabilities discovered"}
              </p>

              <div>
                <div className="text-[10px] uppercase tracking-wider text-text-muted mb-1.5">
                  {a.tools?.length || 0} tools
                </div>
                <div className="flex flex-wrap gap-1">
                  {a.tools?.slice(0, 6).map((t: string) => (
                    <span key={t} className="rounded-md border border-border bg-background px-2 py-0.5 text-[10px] font-mono">
                      {t}
                    </span>
                  ))}
                  {(a.tools?.length || 0) > 6 && (
                    <span className="rounded-md border border-border bg-background px-2 py-0.5 text-[10px] font-mono text-text-muted">
                      +{a.tools.length - 6}
                    </span>
                  )}
                </div>
              </div>

              <Collapsible title="MCP Tools" badge="JSON">
                <pre className="text-[11px] font-mono text-text-secondary overflow-x-auto">
                  {JSON.stringify({ tools: a.tools || [] }, null, 2)}
                </pre>
              </Collapsible>
              <Collapsible title="Logs" badge="tail">
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => fetchLogs(a.name)}
                    className="self-start rounded border border-border px-2 py-0.5 text-[10px] hover:bg-surface-hover"
                  >
                    Refresh logs
                  </button>
                  <pre className="text-[11px] font-mono text-text-secondary leading-relaxed max-h-40 overflow-y-auto">
                    {logs[a.name]?.stdout || `[INFO] Fetch logs to view output for ${a.name}`}
                  </pre>
                </div>
              </Collapsible>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
