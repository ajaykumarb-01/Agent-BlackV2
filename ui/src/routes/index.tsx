import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { InputArea } from "@/components/chat/InputArea";
import { StatusBar } from "@/components/chat/StatusBar";
import { useAppStore, type Message, type TaskEvent } from "@/lib/store";
import { api, type HistoryItem } from "@/lib/api";
import { Trash2, MessageSquarePlus } from "lucide-react";

export const Route = createFileRoute("/")({
  validateSearch: (search: Record<string, unknown>) => ({
    new: search.new === "1" ? "1" : undefined,
    historyId: typeof search.historyId === "string" ? search.historyId : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Chat · Agent Black" },
      {
        name: "description",
        content: "Conversational research interface across CV, NLP, and ML agents.",
      },
    ],
  }),
  component: ChatPage,
});

const FORCE_NEW_CHAT_KEY = "agent-black-force-new-chat";

/** Strip trailing JSON objects/arrays/code-fences from a text string */
function extractTextOnly(text: string): string {
  if (!text) return "";
  let t = text.trim();
  if (isJsonLike(t)) return "";
  const patterns = [/\n\s*\{[\s\S]*$/, /\n\s*\[[\s\S]*$/, /```json[\s\S]*$/];
  for (const p of patterns) {
    const m = t.search(p);
    if (m > 0) t = t.substring(0, m).trim();
  }
  return t || text.trim();
}
function isJsonLike(s: string): boolean {
  const t = s.trim();
  return (t.startsWith("{") && t.endsWith("}")) || (t.startsWith("[") && t.endsWith("]"));
}

function toDisplayString(v: unknown): string | null {
  if (v == null) return null;
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function toSectionValue(v: unknown): string | object | null {
  if (v == null) return null;
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return v as object;
  if (typeof v === "object") return v as object;
  return String(v);
}

const TECH_HINTS = [
  "PyTorch", "TensorFlow", "Keras", "JAX", "scikit-learn", "NumPy", "Pandas", "SciPy", "Polars",
  "LightFM", "BERT", "GPT", "LLM", "Transformer", "SASRec", "LightGCN", "PinSage",
  "GRU4Rec", "MAML", "Prototypical", "SVD", "InstructRec", "P5", "implicit", "Surprise", "RecBole",
  "FAISS", "Annoy", "HNSW", "Qdrant", "Weaviate", "Pinecone", "Milvus", "Redis", "Elasticsearch", "Cassandra",
  "MLflow", "Weights & Biases", "W&B", "Optuna", "DVC", "Airflow", "Kubeflow", "Ray", "TensorBoard", "Hydra",
  "FastAPI", "Flask", "Django", "Streamlit", "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Nginx", "uvicorn", "Pydantic",
  "MovieLens", "MovieLens-1M", "Amazon Reviews", "Yelp", "Spotify", "Goodreads", "IGDB", "Steam", "Netflix", "BookCrossing", "LastFM",
  "CatBoost", "XGBoost", "LightGBM", "Prophet", "spaCy", "Hugging Face", "LangChain", "LlamaIndex",
];

function extractTechStackFromText(text: string): string[] {
  if (!text) return [];
  const found = new Set<string>();
  for (const hint of TECH_HINTS) {
    const re = new RegExp(`\\b${hint.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (re.test(text)) found.add(hint);
  }
  return Array.from(found);
}

function buildSectionsFromReport(report: Record<string, any> | undefined): import("@/lib/store").ReportSections | undefined {
  if (!report) return undefined;

  if (report.error === "not_research_query" || report.error === "no_suitable_agent") {
    return {
      error: String(report.error),
      message: toDisplayString(report.message),
      reason: toDisplayString(report.reason),
      suggestion: toDisplayString(report.suggestion),
      supported_topics: report.supported_topics,
      validation: report.validation,
    };
  }

  const lr = toSectionValue(report.literature_review);
  const ds = toSectionValue(report.datasets);
  const md = toSectionValue(report.models);
  const ev = toSectionValue(report.evaluation_plan);
  const pg = toSectionValue(report.prototype_guidance);

  // Combine LLM-emitted tech_stack with client-side extraction from any text
  const llmStack = Array.isArray(report.tech_stack) ? report.tech_stack.map(String) : [];
  const corpus = [lr, ds, md, ev, pg]
    .filter((v): v is string => typeof v === "string")
    .join("\n");
  const extracted = extractTechStackFromText(corpus);
  const seen = new Set<string>();
  const tech_stack: string[] = [];
  for (const t of [...llmStack, ...extracted]) {
    const key = t.toLowerCase();
    if (!seen.has(key)) { seen.add(key); tech_stack.push(t); }
  }

  return {
    tech_stack,
    parse_warning: report.parse_warning,
    literature_review: lr as import("@/lib/store").SectionValue,
    datasets: ds as import("@/lib/store").SectionValue,
    models: md as import("@/lib/store").SectionValue,
    evaluation_plan: ev as import("@/lib/store").SectionValue,
    prototype_guidance: pg as import("@/lib/store").SectionValue,
  };
}

function historyItemToMessages(h: {
  id: number;
  uuid: string;
  query: string;
  report: {
    content?: unknown;
    literature_review?: unknown;
    datasets?: unknown;
    models?: unknown;
    evaluation_plan?: unknown;
    prototype_guidance?: unknown;
  };
  diagram?: string;
  agents_used: string[];
  created_at: number;
}): Message[] {
  const userMsg: Message = {
    id: `hist-user-${h.id}`,
    role: "user",
    content: h.query,
    timestamp: h.created_at * 1000,
  };
  const sections = {
    ...buildSectionsFromReport(h.report),
  };
  const assistantMsg: Message = {
    id: `hist-asst-${h.id}`,
    role: "assistant",
    query: h.query,
    queryId: h.id,
    content:
      toDisplayString(h.report?.content)
      || (h.report?.error === "not_research_query" || h.report?.error === "no_suitable_agent"
        ? toDisplayString(h.report?.message)
        : null)
      || "Research complete. See report below.",
    timestamp: h.created_at * 1000,
    sections,
    agentsUsed: h.agents_used,
    raw: { query: h.query, report: h.report, diagram: h.diagram },
  };
  return [userMsg, assistantMsg];
}

function ChatPage() {
  const navigate = useNavigate({ from: "/" });
  const search = Route.useSearch();
  const messages = useAppStore((s) => s.messages);
  const addMessage = useAppStore((s) => s.addMessage);
  const updateMessage = useAppStore((s) => s.updateMessage);
  const replaceAllMessages = useAppStore((s) => s.replaceAllMessages);
  const clearMessages = useAppStore((s) => s.clearMessages);
  const endRef = useRef<HTMLDivElement>(null);
  const [sending, setSending] = useState(false);
  const [chatLocked, setChatLocked] = useState(false);

  useEffect(() => {
    if (search.new === "1") {
      window.sessionStorage.setItem(FORCE_NEW_CHAT_KEY, "1");
      clearMessages();
      replaceAllMessages([]);
      setChatLocked(false);
      void navigate({ to: "/", search: {}, replace: true });
      return;
    }

    if (window.sessionStorage.getItem(FORCE_NEW_CHAT_KEY) === "1") {
      window.sessionStorage.removeItem(FORCE_NEW_CHAT_KEY);
      clearMessages();
      replaceAllMessages([]);
      setChatLocked(false);
      return;
    }

    if (search.historyId) {
      api
        .getQueryByUuid(search.historyId)
        .then((item) => {
          replaceAllMessages(historyItemToMessages(item));
          setChatLocked(true);
        })
        .catch(() => undefined);
      return;
    }

    api
      .queryHistory()
      .then((history) => {
        const latestMessages = history.length > 0 ? historyItemToMessages(history[0]) : [];
        replaceAllMessages(latestMessages);
        setChatLocked(latestMessages.length > 0);
      })
      .catch(() => undefined);
  }, [clearMessages, navigate, replaceAllMessages, search.new, search.historyId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  const handleClearChat = async () => {
    clearMessages();
    setChatLocked(false);
    try {
      await api.clearHistory();
    } catch {
      return;
    }
  };

  const handleNewChat = () => {
    window.sessionStorage.setItem(FORCE_NEW_CHAT_KEY, "1");
    clearMessages();
    replaceAllMessages([]);
    setChatLocked(false);
  };

  const handleSubmit = async (text: string) => {
    if (sending || chatLocked) return;
    setSending(true);
    clearMessages();
    setChatLocked(false);
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };
    const placeholderId = crypto.randomUUID();
    const placeholder: Message = {
      id: placeholderId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      pending: true,
      taskProgress: [],
    };
    addMessage(userMsg);
    addMessage(placeholder);

    try {
      const { task_id } = await api.submitQuery(text);

      api.streamTask(
        task_id,
        (ev: TaskEvent) => {
          const state = useAppStore.getState();
          const msg = state.messages.find((m) => m.id === placeholderId);
          const current = msg?.taskProgress || [];
          const merged = [...current.filter((e) => e.step !== ev.step), ev];

          let streamingContent = msg?.streamingContent || "";
          if (ev.status === "complete" && ev.step === "routing") {
            try {
              const parsed = JSON.parse(ev.detail);
              const agents = parsed.agents || [];
              const reasoning = parsed.reasoning || "";
              streamingContent = `Routing to: ${agents.join(", ")}\n\n${reasoning}`;
            } catch {
              streamingContent = ev.detail;
            }
          } else if (ev.status === "complete" && ["research", "solution", "experiment"].includes(ev.step)) {
            try {
              const parsed = JSON.parse(ev.detail);
              const tools = parsed.tools || [];
              const snippet = parsed.snippet || "";
              const toolList = tools.length > 0 ? `Used: ${tools.join(", ")}` : "";
              const section = `\n\n---\n${ev.step.toUpperCase()} Response:\n${toolList}\n${snippet}`;
              streamingContent = (streamingContent || `Agents processing...`) + section;
            } catch {
              streamingContent = (streamingContent || "") + `\n\n${ev.step}: ${ev.detail}`;
            }
          } else if (ev.status === "running") {
            if (ev.step === "routing") {
              streamingContent = "Selecting agents...";
            } else if (["research", "solution", "experiment"].includes(ev.step)) {
              const agentCount = merged.filter((e) => ["research", "solution", "experiment"].includes(e.step)).length;
              if (!streamingContent || streamingContent === "Selecting agents...") {
                streamingContent = `Agents processing...`;
              }
            } else if (ev.step === "aggregating") {
              streamingContent = "Synthesizing final report...";
            }
          }

          updateMessage(placeholderId, { taskProgress: merged, streamingContent });
        },
        (result) => {
          if (result.status === "error" || !result.report) {
            updateMessage(placeholderId, {
              pending: false,
              content: result.error
                ? `Error: ${result.error}`
                : "Query failed. Please check that the LLM provider and agents are configured correctly.",
              raw: result,
            });
            setChatLocked(true);
          } else {
            const r = result.report;
            const sections = buildSectionsFromReport(r);
            const content =
              toDisplayString(r?.content)
              || (r?.error === "not_research_query" || r?.error === "no_suitable_agent" ? toDisplayString(r?.message) : null)
              || "Research complete. See report below.";
            updateMessage(placeholderId, {
              pending: false,
              query: text,
              taskId: result.task_id,
              content,
              sections,
              agentsUsed: result.agents_used?.length ? result.agents_used : undefined,
              streamingContent: undefined,
              raw: result,
            });
            setChatLocked(true);
          }
        },
        (err) => {
          updateMessage(placeholderId, {
            pending: false,
            content: `Error: ${err.message}`,
          });
          setChatLocked(true);
        },
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      updateMessage(placeholderId, {
        pending: false,
        content: `Error: ${message}. Check that agents are running.`,
      });
      setChatLocked(true);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-[860px] min-h-[60vh] flex-col gap-6 px-3 py-4 sm:px-4 sm:py-6">
          <StatusBar />
          {messages.length === 0 ? (
            <EmptyState onPrompt={handleSubmit} />
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-end gap-2">
                <button
                  onClick={handleNewChat}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-text-secondary hover:bg-surface-hover transition-colors"
                >
                  <MessageSquarePlus className="h-3.5 w-3.5" />
                  New Chat
                </button>
                <button
                  onClick={handleClearChat}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-text-secondary hover:bg-surface-hover hover:text-red-400 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear History
                </button>
              </div>
              <div className="flex flex-col gap-6">
                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}
              </div>
            </>
          )}
          <div ref={endRef} />
        </div>
      </div>
      {chatLocked ? (
        <div className="sticky bottom-0 bg-gradient-to-t from-background via-background to-transparent pt-4 pb-4">
          <div className="mx-auto flex max-w-[860px] items-center justify-between gap-3 rounded-xl border border-border bg-surface px-4 py-3 text-sm sm:rounded-2xl">
            <span className="text-text-secondary">
              Research completed. Start a new chat to ask another query.
            </span>
            <button
              onClick={handleNewChat}
              className="inline-flex items-center gap-1.5 rounded-lg bg-foreground px-3 py-2 text-xs text-background hover:opacity-90"
            >
              <MessageSquarePlus className="h-3.5 w-3.5" />
              New Chat
            </button>
          </div>
        </div>
      ) : (
        <InputArea onSubmit={handleSubmit} disabled={sending} />
      )}
    </div>
  );
}

function EmptyState({ onPrompt }: { onPrompt: (text: string) => void }) {
  const samples = [
    "Build an OCR solution for handwritten receipts",
    "Compare modern speech recognition architectures",
    "Design a recommendation system for a niche e-commerce site",
    "Survey methods for few-shot image classification",
  ];
  return (
    <div className="mt-8 flex flex-col items-center text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-surface text-sm font-bold tracking-tighter">
        A·B
      </div>
      <h1 className="text-lg font-semibold tracking-tight sm:text-2xl">
        What should the agents research today?
      </h1>
      <p className="mt-2 max-w-md text-xs text-text-secondary sm:text-sm">
        The orchestrator sends your query through the standard A2A protocol, routes it across CV,
        NLP, and ML agents, and returns a structured research brief.
      </p>
      <div className="mt-4 flex items-center gap-2 text-[11px] text-text-muted">
        <span className="rounded-full border border-border bg-background px-2.5 py-1">
          A2A JSON-RPC
        </span>
        <span className="rounded-full border border-border bg-background px-2.5 py-1">
          Agent Card discovery
        </span>
        <span className="rounded-full border border-border bg-background px-2.5 py-1">
          Structured report
        </span>
      </div>
      <div className="mt-8 grid w-full gap-2 sm:grid-cols-2">
        {samples.map((s) => (
          <button
            key={s}
            onClick={() => onPrompt(s)}
            className="rounded-xl border border-border bg-surface/60 px-4 py-3 text-left text-sm text-foreground hover:bg-surface-hover transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
