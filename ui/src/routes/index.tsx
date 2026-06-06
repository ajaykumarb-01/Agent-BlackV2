import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { InputArea } from "@/components/chat/InputArea";
import { StatusBar } from "@/components/chat/StatusBar";
import { useAppStore, type Message, type TaskEvent } from "@/lib/store";
import { api } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Chat · Agent Black" },
      { name: "description", content: "Conversational research interface across CV, NLP, and ML agents." },
    ],
  }),
  component: ChatPage,
});

function ChatPage() {
  const messages = useAppStore((s) => s.messages);
  const addMessage = useAppStore((s) => s.addMessage);
  const updateMessage = useAppStore((s) => s.updateMessage);
  const replaceAllMessages = useAppStore((s) => s.replaceAllMessages);
  const endRef = useRef<HTMLDivElement>(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.queryHistory().then((history) => {
      const synced = history.flatMap((h) => {
        const userMsg: Message = {
          id: `hist-user-${h.id}`,
          role: "user",
          content: h.query,
          timestamp: h.created_at * 1000,
        };
        const assistantMsg: Message = {
          id: `hist-asst-${h.id}`,
          role: "assistant",
          content: h.report?.content as string || "Research complete.",
          timestamp: h.created_at * 1000,
          sections: {
            literature_review: h.report?.literature_review as string || null,
            datasets: h.report?.datasets as string || null,
            models: h.report?.models as string || null,
            evaluation_plan: h.report?.evaluation_plan as string || null,
            prototype_guidance: h.report?.prototype_guidance as string || null,
          },
          agentsUsed: h.agents_used,
          raw: h.report,
        };
        return [userMsg, assistantMsg];
      });
      replaceAllMessages(synced);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  const handleSubmit = async (text: string) => {
    if (sending) return;
    setSending(true);
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
          updateMessage(placeholderId, {
            taskProgress: [...(useAppStore.getState().messages.find(m => m.id === placeholderId)?.taskProgress || []), ev],
          });
        },
        (result) => {
          updateMessage(placeholderId, {
            pending: false,
            content: result.report?.content as string || "Research complete. See sections below.",
            sections: {
              literature_review: result.report?.literature_review as string || null,
              datasets: result.report?.datasets as string || null,
              models: result.report?.models as string || null,
              evaluation_plan: result.report?.evaluation_plan as string || null,
              prototype_guidance: result.report?.prototype_guidance as string || null,
            },
            agentsUsed: result.agents_used?.length ? result.agents_used : undefined,
            raw: result,
          });
        },
        (err) => {
          updateMessage(placeholderId, {
            pending: false,
            content: `Error: ${err.message}`,
          });
        },
      );
    } catch (err: any) {
      updateMessage(placeholderId, {
        pending: false,
        content: `Error: ${err.message}. Check that agents are running.`,
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-[860px] flex-col gap-6 px-4 py-6">
          <StatusBar />
          {messages.length === 0 ? (
            <EmptyState onPrompt={handleSubmit} />
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>
      <InputArea onSubmit={handleSubmit} disabled={sending} />
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
      <h1 className="text-2xl font-semibold tracking-tight">
        What should the agents research today?
      </h1>
      <p className="mt-2 max-w-md text-sm text-text-secondary">
        The orchestrator routes your query to CV, NLP, and ML agents and returns a structured research brief.
      </p>
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
