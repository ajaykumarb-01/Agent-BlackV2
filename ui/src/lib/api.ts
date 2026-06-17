const BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

async function requestBlob(path: string, options?: RequestInit): Promise<Blob> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.blob();
}

export interface AgentStatus {
  name: string;
  port: number;
  status: string;
  capabilities: string[];
}

export interface SystemStatus {
  host_agent: string;
  agents: Record<string, string>;
  llm_provider: string;
  uptime: number;
}

export interface AgentStats {
  total_queries: number;
  active_agents: number;
  total_agents: number;
  uptime: number;
  avg_response_time: number;
}

export interface TaskEvent {
  step: string;
  status: string;
  detail: string;
  timestamp: number;
}

export interface TaskResult {
  task_id: string;
  query: string;
  status: string;
  report: Record<string, any> | null;
  diagram: string | null;
  agents_used: string[];
  error: string | null;
  created_at: number;
  completed_at: number | null;
  events: TaskEvent[];
}

export interface QueryResponse {
  task_id: string;
  status: string;
}

export interface HistoryItem {
  id: number;
  uuid: string;
  query: string;
  report: Record<string, any>;
  diagram?: string;
  agents_used: string[];
  created_at: number;
}

export interface LLMSettings {
  provider: string;
  model: string;
  api_key_set: boolean;
  base_url?: string;
}

export interface SettingsResponse {
  llm_provider: string;
  providers: Record<string, LLMSettings>;
  agent_urls: Record<string, string>;
}

export interface AgentCardInterface {
  url: string;
  protocolBinding: string;
  protocolVersion?: string;
}

export interface AgentSkill {
  id?: string;
  name?: string;
  description?: string;
  tags?: string[];
  examples?: string[];
  inputModes?: string[];
  outputModes?: string[];
}

export interface AgentCard {
  name: string;
  description?: string;
  version?: string;
  provider?: string;
  supportedInterfaces?: AgentCardInterface[];
  capabilities?: Record<string, any>;
  defaultInputModes?: string[];
  defaultOutputModes?: string[];
  skills?: AgentSkill[];
  icon_url?: string;
  documentation_url?: string;
}

export interface AgentCardResponse {
  card: AgentCard;
  health: string;
  mcp_tools?: Array<{
    name: string;
    description?: string;
    inputSchema?: Record<string, any>;
  }>;
  communication_methods?: Record<string, any>;
}

export interface DiscoAgent {
  name: string;
  url: string;
  port: number;
  capabilities: string[];
  status: string;
  last_seen?: number;
}

export interface SetupStatus {
  complete: boolean;
  steps: { step: string; completed: boolean; completed_at?: number }[];
}

export interface LogEntry {
  time: string;
  level: string;
  message: string;
  service: string;
}

export interface LogsResponse {
  entries: LogEntry[];
  total: number;
  offset: number;
  limit: number;
}

export const api = {
  status: () => request<SystemStatus>("/status"),
  agentStats: () => request<AgentStats>("/agents/stats"),

  submitQuery: (query: string) =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  streamTask: (
    taskId: string,
    onEvent: (ev: TaskEvent) => void,
    onDone: (result: TaskResult) => void,
    onError: (err: Error) => void,
  ) => {
    const controller = new AbortController();

    const run = async () => {
      try {
        const res = await fetch(`${BASE}/query/stream/${taskId}`, { signal: controller.signal });
        if (!res.ok || !res.body) {
          onError(new Error(`SSE ${res.status}`));
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);
                if (eventType === "done") {
                  onDone(parsed);
                } else {
                  onEvent(parsed);
                }
              } catch {
                // skip malformed JSON lines
              }
              eventType = "";
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          onError(err);
        }
      }
    };

    run();
    return () => controller.abort();
  },

  getTask: (taskId: string) => request<TaskResult>(`/query/task/${taskId}`),
  downloadReportPdf: (data: {
    query?: string;
    report?: Record<string, any>;
    agents_used?: string[];
    task_id?: string;
    query_id?: number;
  }) =>
    requestBlob("/query/report/pdf", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  queryHistory: () => request<HistoryItem[]>("/query/history"),
  getQueryById: (id: number) => request<HistoryItem>(`/query/${id}`),
  getQueryByUuid: (uuid: string) => request<HistoryItem>(`/query/uuid/${uuid}`),
  clearHistory: () => request<{ message: string }>("/query/history", { method: "DELETE" }),

  getSettings: () => request<SettingsResponse>("/settings"),
  updateSettings: (data: Record<string, any>) =>
    request<{ message: string }>("/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  discoverAgents: () =>
    request<{ agents: Record<string, AgentCard | { error: string }> }>("/agents/discover"),
  getDiscoveredAgents: () => request<{ agents: DiscoAgent[] }>("/agents/discovered"),
  getAgentCard: (key: string) => request<AgentCardResponse>(`/agents/${key}/card`),
  getAgentLogs: (name: string) =>
    request<{ name: string; stdout: string; stderr: string }>(`/agents/${name}/logs`),

  getLogs: (params?: { level?: string; service?: string; search?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.level) q.set("level", params.level);
    if (params?.service) q.set("service", params.service);
    if (params?.search) q.set("search", params.search);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return request<LogsResponse>(`/logs${qs ? `?${qs}` : ""}`);
  },
  getLogFiles: () => request<{ files: { service: string; size_bytes: number }[] }>("/logs/files"),

  startAgents: () => request<any>("/agents/start", { method: "POST" }),
  stopAgents: () => request<any>("/agents/stop", { method: "POST" }),

  getDiagramAgentFlow: (query?: string) =>
    request<{ diagram: string; description: string }>("/diagram/agent-flow", {
      method: "POST",
      body: JSON.stringify({ query: query || "" }),
    }),
  getDiagramTechStack: () =>
    request<{ diagram: string; description: string }>("/diagram/tech-stack", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getDiagramFromReport: (data: {
    query: string;
    report: Record<string, any>;
    agents_used?: string[];
    events?: { step: string; status: string; detail: string; timestamp: number }[];
  }) =>
    request<{ diagram: string; description: string }>("/diagram/from-report", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  setupStatus: () => request<SetupStatus>("/setup/status"),
  completeSetupStep: (step: string) =>
    request<{ steps: any[] }>("/setup/step", {
      method: "POST",
      body: JSON.stringify({ step }),
    }),
  completeSetup: (config: {
    llm_provider: string;
    api_key: string;
    model: string;
    base_url?: string;
    research_agent_url?: string;
    solution_agent_url?: string;
    experiment_agent_url?: string;
  }) =>
    request<{ message: string }>("/setup/complete", {
      method: "POST",
      body: JSON.stringify(config),
    }),
};
