import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

let initialized = false;
if (!initialized) {
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "loose",
    themeVariables: {
      primaryColor: "#4A90D9",
      primaryTextColor: "#e0e0e0",
      primaryBorderColor: "#e0e0e0",
      lineColor: "#666",
      secondaryColor: "#1a1a2e",
      tertiaryColor: "#16213e",
      fontFamily: "monospace",
      fontSize: "13px",
    },
  });
  initialized = true;
}

interface MermaidDiagramProps {
  code: string;
  zoom?: number;
  onZoomChange?: (zoom: number) => void;
}

export function MermaidDiagram({ code, zoom = 1, onZoomChange }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!code || !ref.current) return;
    setError("");
    setSvg("");

    const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    mermaid.render(id, code).then(
      ({ svg }) => setSvg(svg),
      (err) => setError(String(err?.message || err)),
    );
  }, [code]);

  useEffect(() => {
    const el = ref.current;
    if (!el || !onZoomChange) return;
    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        onZoomChange(Math.min(5, Math.max(0.2, zoom + delta)));
      }
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoom, onZoomChange]);

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
        <p className="text-xs text-red-400 font-mono mb-2">Mermaid render error:</p>
        <pre className="text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap">{error}</pre>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className="mermaid-diagram flex justify-center overflow-x-auto"
      style={{ transform: `scale(${zoom})`, transformOrigin: "center top" }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
