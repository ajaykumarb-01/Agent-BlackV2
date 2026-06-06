import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Download, ZoomIn, ZoomOut, Workflow, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export const Route = createFileRoute("/diagram")({
  head: () => ({ meta: [      { title: "Diagram · Agent Black" }] }),
  component: DiagramPage,
});

const tabs = ["Agent Flow", "Tech Stack"] as const;

function DiagramPage() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("Agent Flow");
  const [diagram, setDiagram] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const fetchDiagram = tab === "Agent Flow" ? api.getDiagramAgentFlow : api.getDiagramTechStack;
    fetchDiagram().then((res) => {
      setDiagram(res.diagram);
    }).catch(() => {
      setDiagram("");
    }).finally(() => setLoading(false));
  }, [tab]);

  return (
    <div className="mx-auto w-full max-w-[1100px] px-4 py-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Diagram</h1>
        <div className="inline-flex rounded-lg border border-border bg-surface p-0.5 text-xs">
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

      <div className="relative min-h-[520px] rounded-xl border border-dashed border-border bg-surface/50 flex items-center justify-center">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading diagram...
          </div>
        ) : diagram ? (
          <pre className="p-6 text-xs font-mono text-text-secondary overflow-x-auto w-full max-h-[600px] leading-relaxed">
            {diagram}
          </pre>
        ) : (
          <div className="text-center">
            <Workflow className="mx-auto mb-3 h-10 w-10 text-text-muted" />
            <p className="text-sm font-medium">{tab} diagram</p>
            <p className="mt-1 text-xs text-text-muted">
              Diagram will render here once the backend generates it.
            </p>
          </div>
        )}

        {diagram && (
          <div className="absolute bottom-4 right-4 flex items-center gap-1 rounded-lg border border-border bg-background p-1 shadow-sm">
            <IconBtn><ZoomOut className="h-4 w-4" /></IconBtn>
            <IconBtn><ZoomIn className="h-4 w-4" /></IconBtn>
            <span className="mx-1 h-5 w-px bg-border" />
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
            >
              <Download className="h-4 w-4" />
            </IconBtn>
          </div>
        )}
      </div>
    </div>
  );
}

function IconBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md p-1.5 text-text-secondary hover:bg-surface-hover hover:text-foreground"
    >
      {children}
    </button>
  );
}
