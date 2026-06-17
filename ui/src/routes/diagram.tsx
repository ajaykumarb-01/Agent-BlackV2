import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, useCallback } from "react";
import { Download, ZoomIn, ZoomOut, Maximize2, Minimize2, Workflow, Loader2, RefreshCw, ImageDown } from "lucide-react";
import { api } from "@/lib/api";
import { MermaidDiagram, type MermaidDiagramHandle } from "@/components/shared/MermaidDiagram";
import { useAppStore } from "@/lib/store";

export const Route = createFileRoute("/diagram")({
  head: () => ({ meta: [{ title: "Diagram · Agent Black" }] }),
  component: DiagramPage,
});

const tabs = ["Project Flow", "Tech Stack", "Architecture"] as const;

function DiagramPage() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("Project Flow");
  const [diagram, setDiagram] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);
  const [downloadPngBusy, setDownloadPngBusy] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const diagramRef = useRef<MermaidDiagramHandle>(null);

  const messages = useAppStore((s) => s.messages);

  // Get the latest assistant message with report data
  const latestReport = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role === "assistant" && m.sections && Object.values(m.sections).some(Boolean)) {
        return m;
      }
    }
    return null;
  })();

  const loadDiagram = useCallback(async () => {
    setLoading(true);
    setDiagram("");
    setDescription("");
    try {
      // Build report data from latest assistant message
      const reportData: Record<string, any> = {};
      if (latestReport?.sections) {
        for (const [k, v] of Object.entries(latestReport.sections)) {
          if (v) {
            try { reportData[k] = typeof v === "string" ? JSON.parse(v) : v; } catch { reportData[k] = v; }
          }
        }
      }
      // Include tech_stack and tools_used from raw data
      const raw = (latestReport?.raw as Record<string, any>) || {};
      if (raw?.report?.tech_stack) {
        reportData.tech_stack = raw.report.tech_stack;
      }
      if (raw?.report?.tools_used) {
        reportData.tools_used = raw.report.tools_used;
      }

      const userMsg = messages.find(
        (m) => m.role === "user" && m.timestamp <= (latestReport?.timestamp || Infinity),
      );
      const queryText = userMsg?.content || "";
      const agentsUsed = latestReport?.agentsUsed || [];
      const events = latestReport?.taskProgress || [];

      if (tab === "Project Flow" && latestReport) {
        const res = await api.getDiagramFromReport({
          query: queryText || "research query",
          report: reportData,
          agents_used: agentsUsed,
          events,
          raw: raw || undefined,
        });
        setDiagram(res.diagram);
        setDescription(res.description);
      } else if (tab === "Tech Stack") {
        const res = await api.getDiagramTechStack({
          report: latestReport ? reportData : undefined,
        });
        setDiagram(res.diagram);
        setDescription(res.description);
      } else {
        const res = await api.getDiagramAgentFlow({
          query: queryText,
          report: latestReport ? reportData : undefined,
          agents_used: latestReport ? agentsUsed : undefined,
          events: latestReport ? events : undefined,
        });
        setDiagram(res.diagram);
        setDescription(res.description);
      }
    } catch {
      setDiagram("");
    } finally {
      setLoading(false);
    }
  }, [tab, latestReport, messages]);

  useEffect(() => { loadDiagram(); }, [loadDiagram]);

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
  const zoomLabel = `${Math.round(zoom * 100)}%`;

  const handleDownloadPng = useCallback(async () => {
    if (!diagramRef.current) return;
    setDownloadPngBusy(true);
    try {
      await diagramRef.current.downloadPng(`${tab.toLowerCase().replace(/\s+/g, "-")}-diagram.png`);
    } catch (err) {
      console.error("PNG download failed:", err);
    } finally {
      setDownloadPngBusy(false);
    }
  }, [tab]);

  return (
    <div className="mx-auto w-full max-w-[1100px] px-3 py-4 sm:px-4 sm:py-6 flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold tracking-tight">Diagram</h1>
          {tab === "Project Flow" && latestReport && (
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
              Live Report
            </span>
          )}
        </div>
        <div className="inline-flex flex-wrap rounded-lg border border-border bg-surface p-0.5 text-xs">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-md px-3 py-1.5 transition-colors ${
                t === tab ? "bg-foreground text-background" : "text-text-secondary hover:bg-surface-hover"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {description && (
        <p className="text-xs text-text-muted">{description}</p>
      )}

      <div
        ref={containerRef}
        className={`relative min-h-[300px] rounded-xl border border-dashed border-border bg-surface/50 flex items-center justify-center sm:min-h-[520px] ${
          fullscreen
            ? "fixed inset-0 z-50 min-h-screen rounded-none border-0 bg-background"
            : ""
        }`}
      >
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating diagram...
          </div>
        ) : diagram ? (
          <div className="h-full w-full p-6">
            <MermaidDiagram ref={diagramRef} code={diagram} zoom={zoom} onZoomChange={setZoom} />
          </div>
        ) : (
          <div className="text-center">
            <Workflow className="mx-auto mb-3 h-10 w-10 text-text-muted" />
            <p className="text-sm font-medium">
              {tab === "Project Flow" && !latestReport
                ? "No project report yet"
                : `${tab} diagram`}
            </p>
            <p className="mt-1 text-xs text-text-muted">
              {tab === "Project Flow" && !latestReport
                ? "Run a query first to generate a project-specific diagram."
                : "Diagram will render here once available."}
            </p>
          </div>
        )}

        {diagram && (
          <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-lg border border-border bg-background p-1 shadow-sm sm:bottom-4 sm:right-4">
            <IconBtn onClick={loadDiagram} title="Refresh">
              <RefreshCw className="h-4 w-4" />
            </IconBtn>
            <IconBtn onClick={zoomOut} title="Zoom out">
              <ZoomOut className="h-4 w-4" />
            </IconBtn>
            <span className="px-1 text-[10px] font-mono text-text-secondary min-w-[3ch] text-center">
              {zoomLabel}
            </span>
            <IconBtn onClick={zoomIn} title="Zoom in">
              <ZoomIn className="h-4 w-4" />
            </IconBtn>
            <span className="mx-1 h-5 w-px bg-border" />
            <IconBtn onClick={handleFullscreen} title={fullscreen ? "Exit fullscreen" : "Fullscreen"}>
              {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </IconBtn>
            <span className="mx-1 h-5 w-px bg-border" />
            <IconBtn
              onClick={handleDownloadPng}
              title="Download PNG"
            >
              {downloadPngBusy ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ImageDown className="h-4 w-4" />
              )}
            </IconBtn>
            <IconBtn
              onClick={() => {
                const blob = new Blob([diagram], { type: "text/plain" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${tab.toLowerCase().replace(" ", "-")}.mmd`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              title="Download .mmd (source)"
            >
              <Download className="h-4 w-4" />
            </IconBtn>
          </div>
        )}
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
      className="rounded-md p-1.5 text-text-secondary hover:bg-surface-hover hover:text-foreground"
    >
      {children}
    </button>
  );
}
