import ReactMarkdown from "react-markdown";
import { Check, Copy, FileText, Workflow, Braces } from "lucide-react";
import { useState } from "react";
import type { Message } from "@/lib/store";
import { AgentsUsedBadge } from "./AgentsUsedBadge";
import { ReportSections } from "./ReportSection";
import { TaskProgress } from "./TaskProgress";

type View = "report" | "diagram" | "raw";

export function MessageBubble({ message }: { message: Message }) {
  const [view, setView] = useState<View>("report");
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(message.content || JSON.stringify(message.raw, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end fade-in-up">
        <div className="max-w-[80%] rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-primary-foreground text-[15px] leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in-up">
      <div className="flex items-start gap-3">
        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-surface text-[10px] font-bold tracking-tighter">
          A·B
        </div>
        <div className="flex-1 min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <AgentsUsedBadge agents={message.agentsUsed} />
            {message.reasoning && (
              <span className="text-[11px] text-text-muted italic">
                {message.reasoning}
              </span>
            )}
          </div>

          {message.pending ? (
            <>
              <TaskProgress events={message.taskProgress || []} />
              <LoadingDots />
            </>
          ) : (
            <>
              {message.content && (
                <div className="md-body mb-3 rounded-2xl rounded-tl-md bg-surface px-4 py-3">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              <div className="mb-3 inline-flex rounded-lg border border-border bg-background p-0.5 text-xs">
                <ToolbarBtn active={view === "report"} onClick={() => setView("report")} icon={<FileText className="h-3.5 w-3.5" />}>
                  Report
                </ToolbarBtn>
                <ToolbarBtn active={view === "diagram"} onClick={() => setView("diagram")} icon={<Workflow className="h-3.5 w-3.5" />}>
                  Diagram
                </ToolbarBtn>
                <ToolbarBtn active={view === "raw"} onClick={() => setView("raw")} icon={<Braces className="h-3.5 w-3.5" />}>
                  Raw JSON
                </ToolbarBtn>
                <button
                  onClick={copy}
                  className="ml-1 inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-text-secondary hover:bg-surface-hover"
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>

              {view === "report" && message.sections && (
                <ReportSections sections={message.sections} />
              )}
              {view === "diagram" && <DiagramPlaceholder />}
              {view === "raw" && (
                <pre className="rounded-lg border border-border bg-surface p-4 text-xs font-mono overflow-x-auto max-h-96">
                  {JSON.stringify(message.raw ?? message, null, 2)}
                </pre>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ToolbarBtn({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 transition-colors ${
        active
          ? "bg-foreground text-background"
          : "text-text-secondary hover:bg-surface-hover"
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

function LoadingDots() {
  return (
    <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-md bg-surface px-4 py-4 w-fit">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="loading-dot h-1.5 w-1.5 rounded-full bg-text-secondary"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

function DiagramPlaceholder() {
  return (
    <div className="rounded-lg border border-dashed border-border bg-surface/50 p-8 text-center">
      <Workflow className="mx-auto mb-2 h-6 w-6 text-text-muted" />
      <p className="text-sm text-text-secondary">Mermaid diagram renders here</p>
      <p className="mt-1 text-xs text-text-muted">
        Connect <code className="font-mono">/api/diagram/agent-flow</code> to populate
      </p>
    </div>
  );
}
