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

function buildSectionsFromReport(report: Record<string, any> | undefined) {
  if (!report) return undefined;

  if (report.error === "not_research_query") {
    return {
      error: String(report.error),
      message: toDisplayString(report.message),
      reason: toDisplayString(report.reason),
      suggestion: toDisplayString(report.suggestion),
      supported_topics: report.supported_topics,
      validation: report.validation,
    };
  }

  return {
    literature_review: toDisplayString(report.literature_review),
    datasets: toDisplayString(report.datasets),
    models: toDisplayString(report.models),
    evaluation_plan: toDisplayString(report.evaluation_plan),
    prototype_guidance: toDisplayString(report.prototype_guidance),
  };
}

function historyItemToMessages(h: {
  id: number;
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
      || (h.report?.error === "not_research_query"
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

function latestHistoryPair(history: HistoryItem[]): Message[] {
  const latest = history.at(-1);
  return latest ? historyItemToMessages(latest) : [];
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

    api
      .queryHistory()
      .then((history) => {
        const latestMessages = latestHistoryPair(history);
        replaceAllMessages(latestMessages);
        setChatLocked(latestMessages.length > 0);
      })
      .catch(() => undefined);
  }, [clearMessages, navigate, replaceAllMessages, search.new]);

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
          const current =
            useAppStore.getState().messages.find((m) => m.id === placeholderId)?.taskProgress || [];
          const merged = [...current.filter((e) => e.step !== ev.step), ev];
          updateMessage(placeholderId, { taskProgress: merged });
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
              || (r?.error === "not_research_query" ? toDisplayString(r?.message) : null)
              || "Research complete. See report below.";
            updateMessage(placeholderId, {
              pending: false,
              query: text,
              taskId: result.task_id,
              content,
              sections,
              agentsUsed: result.agents_used?.length ? result.agents_used : undefined,
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
        <div className="mx-auto flex w-full max-w-[860px] flex-col gap-6 px-3 py-4 sm:px-4 sm:py-6">
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
