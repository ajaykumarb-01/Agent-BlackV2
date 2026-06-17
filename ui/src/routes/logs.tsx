import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, useCallback, useRef } from "react";
import { api, type LogEntry, type LogsResponse } from "@/lib/api";
import {
  Search,
  RefreshCw,
  AlertTriangle,
  Info,
  Bug,
  XCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Filter,
  Pause,
  Play,
} from "lucide-react";

export const Route = createFileRoute("/logs")({
  head: () => ({ meta: [{ title: "Logs · Agent Black" }] }),
  component: LogsPage,
});

const LEVELS = ["ALL", "INFO", "DEBUG", "WARNING", "ERROR"] as const;
type LevelFilter = (typeof LEVELS)[number];

const SERVICES = [
  "ALL",
  "control-panel",
  "research-agent",
  "solution-agent",
  "experiment-agent",
] as const;
type ServiceFilter = (typeof SERVICES)[number];

const levelColors: Record<string, string> = {
  INFO: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  DEBUG: "text-gray-400 bg-gray-500/10 border-gray-500/20",
  WARNING: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  ERROR: "text-red-400 bg-red-500/10 border-red-500/20",
  CRITICAL: "text-red-300 bg-red-600/10 border-red-600/20",
};

const levelIcons: Record<string, typeof Info> = {
  INFO: Info,
  DEBUG: Bug,
  WARNING: AlertTriangle,
  ERROR: XCircle,
  CRITICAL: XCircle,
};

function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("ALL");
  const [serviceFilter, setServiceFilter] = useState<ServiceFilter>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: {
        level?: string;
        service?: string;
        search?: string;
        limit?: number;
        offset?: number;
      } = { limit: 500 };
      if (levelFilter !== "ALL") params.level = levelFilter;
      if (serviceFilter !== "ALL") params.service = serviceFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const res: LogsResponse = await api.getLogs(params);
      setLogs(res.entries);
      setTotal(res.total);
    } catch {
      setLogs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [levelFilter, serviceFilter, searchQuery]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 5000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, fetchLogs]);

  const isNearBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 100;
  }, []);

  useEffect(() => {
    if (autoRefresh && scrollRef.current && isNearBottom()) {
      requestAnimationFrame(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      });
    }
  }, [logs, autoRefresh, isNearBottom]);

  const toggleExpand = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="mx-auto w-full max-w-[1100px] px-3 py-4 sm:px-4 sm:py-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Logs</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {total.toLocaleString()} entries
            {loading && <span className="ml-2 text-text-muted">loading...</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
              autoRefresh
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-border hover:bg-surface-hover"
            }`}
          >
            {autoRefresh ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            {autoRefresh ? "Live" : "Auto-refresh"}
          </button>
          <button
            onClick={fetchLogs}
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-surface-hover transition-colors"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-4 flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-text-muted">
            <Filter className="h-3 w-3" />
            Level
          </div>
          <div className="flex gap-1">
            {LEVELS.map((l) => (
              <button
                key={l}
                onClick={() => setLevelFilter(l)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium border transition-colors ${
                  levelFilter === l
                    ? l === "ALL"
                      ? "border-foreground/30 bg-foreground/10 text-foreground"
                      : (levelColors[l] ?? "border-border bg-surface-hover text-foreground")
                    : "border-transparent text-text-muted hover:bg-surface-hover"
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          <div className="h-4 w-px bg-border" />

          <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-text-muted">
            <FileText className="h-3 w-3" />
            Service
          </div>
          <div className="relative">
            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value as ServiceFilter)}
              className="appearance-none rounded-md border border-border bg-background px-3 py-1 pr-7 text-xs font-medium outline-none focus:border-foreground/40 cursor-pointer"
            >
              {SERVICES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-text-muted" />
          </div>

          <div className="h-4 w-px bg-border" />

          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-xs outline-none focus:border-foreground/40 placeholder:text-text-muted"
            />
          </div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="rounded-xl border border-border bg-surface overflow-hidden max-h-[70vh] overflow-y-auto"
      >
        {logs.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <FileText className="h-8 w-8 mb-2 opacity-40" />
            <p className="text-sm">No log entries found</p>
            <p className="text-xs mt-1">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {logs.map((entry, idx) => {
              const Icon = levelIcons[entry.level] ?? Info;
              const isExpanded = expanded.has(idx);
              const isLong = entry.message.length > 120;
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-2 px-3 py-2 text-xs font-mono transition-colors hover:bg-foreground/[0.02] ${entry.level === "ERROR" || entry.level === "CRITICAL" ? "bg-red-500/[0.03]" : ""}`}
                >
                  <span className="w-16 shrink-0 text-text-muted tabular-nums">{entry.time}</span>
                  <span
                    className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider shrink-0 ${
                      levelColors[entry.level] ?? "text-text-muted border-border"
                    }`}
                  >
                    <Icon className="h-2.5 w-2.5" />
                    {entry.level}
                  </span>
                  <span className="shrink-0 rounded-md border border-border bg-background px-1.5 py-0.5 text-[10px] text-text-secondary">
                    {entry.service}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-text-secondary break-all ${
                        !isExpanded && isLong ? "line-clamp-2" : ""
                      }`}
                    >
                      {entry.message}
                    </span>
                    {isLong && (
                      <button
                        onClick={() => toggleExpand(idx)}
                        className="ml-1.5 inline-flex items-center gap-0.5 text-[10px] text-text-muted hover:text-foreground"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="h-2.5 w-2.5" /> less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-2.5 w-2.5" /> more
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
