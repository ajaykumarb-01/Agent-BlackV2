import ReactMarkdown from "react-markdown";
import { Check, Copy, FileDown, FileText, Workflow, Braces, Loader2, ZoomIn, ZoomOut, Maximize2, Minimize2 } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import type { Message } from "@/lib/store";
import { api } from "@/lib/api";
import { AgentsUsedBadge } from "./AgentsUsedBadge";
import { ReportSections } from "./ReportSection";
import { TaskProgress } from "./TaskProgress";
import { MermaidDiagram } from "@/components/shared/MermaidDiagram";

type View = "report" | "diagram" | "raw";

function isJsonString(s: string): boolean {
  if (!s) return false;
  const trimmed = s.trim();
  return (trimmed.startsWith("{") || trimmed.startsWith("[")) && (trimmed.endsWith("}") || trimmed.endsWith("]"));
}

function formatContent(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  let text = raw.trim();
  if (!text) return null;

  // If the entire string is JSON, return null (sections handle it)
  if (isJsonString(text)) return null;

  // Strip trailing JSON: object/array on new line, or code fence
  const jsonPatterns = [
    /\n\s*\{[\s\S]*$/,   // JSON object
    /\n\s*\[[\s\S]*$/,   // JSON array
    /```json[\s\S]*$/,   // Code fence
  ];
  for (const p of jsonPatterns) {
    const m = text.search(p);
    if (m > 0) {
      text = text.substring(0, m).trim();
    }
  }

  if (!text) return null;
  return text;
}

export function MessageBubble({ message }: { message: Message }) {
  const [view, setView] = useState<View>("report");
  const [copied, setCopied] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(message.content || JSON.stringify(message.raw, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  const downloadPdf = async () => {
    const report = (message.raw as { report?: Record<string, any> } | undefined)?.report;
    if (!report) return;

    setDownloadingPdf(true);
    try {
      const blob = await api.downloadReportPdf({
        query: message.query || ((message.raw as { query?: string } | undefined)?.query ?? "Research Report"),
        report,
        agents_used: message.agentsUsed || [],
      });
      const fileNameBase = (message.query || "research-report")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 60) || "research-report";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${fileNameBase}-report.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end fade-in-up">
        <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-primary px-3 py-2 text-primary-foreground text-sm leading-relaxed sm:max-w-[80%] sm:px-4 sm:py-2.5 sm:text-[15px]">
          {message.content}
      </div>
    </div>
  );
}

function IconBtn({
  children,
  onClick,
  title,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  title?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="rounded-md p-1 text-text-secondary hover:bg-surface-hover hover:text-foreground"
    >
      {children}
    </button>
  );
}

  const displayContent = formatContent(message.content);
  const hasSections = message.sections && Object.values(message.sections).some(Boolean);

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
              {displayContent && (
                <div className="md-body mb-3 rounded-2xl rounded-tl-md bg-surface px-3 py-2.5 sm:px-4 sm:py-3">
                  <ReactMarkdown>{displayContent}</ReactMarkdown>
                </div>
              )}

              <div className="mb-3 inline-flex flex-wrap rounded-lg border border-border bg-background p-0.5 text-xs">
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
                {!!(message.raw as { report?: Record<string, any> } | undefined)?.report && (
                  <button
                    onClick={downloadPdf}
                    disabled={downloadingPdf}
                    className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-text-secondary hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {downloadingPdf ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileDown className="h-3.5 w-3.5" />}
                    {downloadingPdf ? "Preparing PDF" : "Download PDF"}
                  </button>
                )}
              </div>

              {view === "report" && message.sections && (
                <ReportSections sections={message.sections} />
              )}
              {view === "diagram" && <DiagramView message={message} />}
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

function DiagramView({ message }: { message: Message }) {
  const [diagram, setDiagram] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [zoom, setZoom] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const hasReport = message.sections && Object.values(message.sections).some(Boolean);
        if (hasReport) {
          const reportData: Record<string, any> = {};
          if (message.sections) {
            for (const [k, v] of Object.entries(message.sections)) {
              if (v) {
                try { reportData[k] = JSON.parse(v); } catch { reportData[k] = v; }
              }
            }
          }
          // Find the user query that preceded this message
          const userMsg = (message.raw as any)?.query || "";
          const res = await api.getDiagramFromReport({
            query: userMsg,
            report: reportData,
            agents_used: message.agentsUsed || [],
            events: message.taskProgress || [],
          });
          if (!cancelled) setDiagram(res.diagram);
        } else {
          const res = await api.getDiagramAgentFlow();
          if (!cancelled) setDiagram(res.diagram);
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to generate diagram");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [message]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && fullscreen) setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fullscreen]);

  const handleFullscreen = useCallback(() => {
    if (!fullscreen && containerRef.current) {
      containerRef.current.requestFullscreen?.();
    } else if (fullscreen) {
      document.exitFullscreen?.();
    }
    setFullscreen((f) => !f);
  }, [fullscreen]);

  const zoomIn = useCallback(() => setZoom((z) => Math.min(5, z + 0.2)), []);
  const zoomOut = useCallback(() => setZoom((z) => Math.max(0.2, z - 0.2)), []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border bg-surface/50 p-6 text-sm text-text-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        Generating project diagram...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-center">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    );
  }

  if (!diagram) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface/50 p-8 text-center">
        <Workflow className="mx-auto mb-2 h-6 w-6 text-text-muted" />
        <p className="text-sm text-text-secondary">No diagram available</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative rounded-lg border border-border bg-surface/50 ${
        fullscreen ? "fixed inset-0 z-50 rounded-none border-0 bg-background p-4" : "p-4"
      }`}
    >
      <div className="w-full">
        <MermaidDiagram code={diagram} zoom={zoom} onZoomChange={setZoom} />
      </div>
      <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-lg border border-border bg-background p-1 shadow-sm">
        <IconBtn onClick={zoomOut} title="Zoom out">
          <ZoomOut className="h-3.5 w-3.5" />
        </IconBtn>
        <span className="px-1 text-[10px] font-mono text-text-secondary min-w-[3ch] text-center">
          {Math.round(zoom * 100)}%
        </span>
        <IconBtn onClick={zoomIn} title="Zoom in">
          <ZoomIn className="h-3.5 w-3.5" />
        </IconBtn>
        <span className="mx-0.5 h-4 w-px bg-border" />
        <IconBtn onClick={handleFullscreen} title={fullscreen ? "Exit fullscreen" : "Fullscreen"}>
          {fullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
        </IconBtn>
      </div>
    </div>
  );
}

function IconBtn({
  children,
  onClick,
  title,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  title?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="rounded-md p-1 text-text-secondary hover:bg-surface-hover hover:text-foreground"
    >
      {children}
    </button>
  );
}
