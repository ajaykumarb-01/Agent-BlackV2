import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import mermaid from "mermaid";
import { useDarkMode } from "@/hooks/use-dark-mode";

const baseThemeVariables = {
  fontFamily: "monospace",
  fontSize: "13px",
};

interface MermaidDiagramProps {
  code: string;
  zoom?: number;
  onZoomChange?: (zoom: number) => void;
}

export interface MermaidDiagramHandle {
  downloadPng: (filename: string) => Promise<void>;
  getSvgElement: () => SVGElement | null;
}

export const MermaidDiagram = forwardRef<MermaidDiagramHandle, MermaidDiagramProps>(
  function MermaidDiagram({ code, zoom = 1, onZoomChange }, ref) {
    const containerRef = useRef<HTMLDivElement>(null);
    const svgWrapperRef = useRef<HTMLDivElement>(null);
    const dragState = useRef<{ x: number; y: number; left: number; top: number } | null>(null);
    const [svg, setSvg] = useState("");
    const [error, setError] = useState("");
    const { isDark } = useDarkMode();

    useImperativeHandle(ref, () => ({
      downloadPng: async (filename: string) => {
        const svgEl = svgWrapperRef.current?.querySelector("svg");
        if (!svgEl) throw new Error("No SVG rendered");
        await downloadSvgAsPng(svgEl, filename);
      },
      getSvgElement: () => svgWrapperRef.current?.querySelector("svg") ?? null,
    }));

    useEffect(() => {
      if (!code || !containerRef.current) return;
      setError("");
      setSvg("");

      mermaid.initialize({
        startOnLoad: false,
        theme: isDark ? "dark" : "default",
        securityLevel: "loose",
        themeVariables: isDark
          ? {
              ...baseThemeVariables,
              primaryColor: "#4A90D9",
              primaryTextColor: "#e0e0e0",
              primaryBorderColor: "#e0e0e0",
              lineColor: "#666",
              secondaryColor: "#1a1a2e",
              tertiaryColor: "#16213e",
            }
          : {
              ...baseThemeVariables,
              primaryColor: "#4A90D9",
              primaryTextColor: "#1a1a1a",
              primaryBorderColor: "#1a1a1a",
              lineColor: "#555",
              secondaryColor: "#f5f5f5",
              tertiaryColor: "#ebebeb",
            },
      });

      const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      mermaid.render(id, code).then(
        ({ svg }) => setSvg(svg),
        (err) => setError(String(err?.message || err)),
      );
    }, [code, isDark]);

    useEffect(() => {
      const el = containerRef.current;
      if (!el) return;
      el.scrollTo({ left: 0, top: 0 });
    }, [code]);

    useEffect(() => {
      const el = containerRef.current;
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

    useEffect(() => {
      const el = containerRef.current;
      if (!el) return;

      const onPointerDown = (e: PointerEvent) => {
        if (e.button !== 0) return;
        dragState.current = {
          x: e.clientX,
          y: e.clientY,
          left: el.scrollLeft,
          top: el.scrollTop,
        };
        el.setPointerCapture?.(e.pointerId);
        el.style.cursor = "grabbing";
      };

      const onPointerMove = (e: PointerEvent) => {
        const drag = dragState.current;
        if (!drag) return;
        el.scrollLeft = drag.left - (e.clientX - drag.x);
        el.scrollTop = drag.top - (e.clientY - drag.y);
      };

      const stopDragging = (e: PointerEvent) => {
        if (!dragState.current) return;
        dragState.current = null;
        el.releasePointerCapture?.(e.pointerId);
        el.style.cursor = svg ? "grab" : "default";
      };

      el.addEventListener("pointerdown", onPointerDown);
      el.addEventListener("pointermove", onPointerMove);
      el.addEventListener("pointerup", stopDragging);
      el.addEventListener("pointercancel", stopDragging);
      el.addEventListener("pointerleave", stopDragging);

      el.style.cursor = svg ? "grab" : "default";

      return () => {
        el.removeEventListener("pointerdown", onPointerDown);
        el.removeEventListener("pointermove", onPointerMove);
        el.removeEventListener("pointerup", stopDragging);
        el.removeEventListener("pointercancel", stopDragging);
        el.removeEventListener("pointerleave", stopDragging);
        el.style.cursor = "default";
      };
    }, [svg]);

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
        ref={containerRef}
        className="mermaid-diagram overflow-auto touch-none select-none"
      >
        <div
          ref={svgWrapperRef}
          className="flex min-w-max justify-center p-2 [&_svg]:h-auto [&_svg]:max-w-none [&_svg]:overflow-visible"
          style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>
    );
  },
);

async function downloadSvgAsPng(svgEl: SVGElement, filename: string) {
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svgEl);
  const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const svgUrl = URL.createObjectURL(svgBlob);

  const svgRect = svgEl.getBoundingClientRect();
  const scale = 2;
  const width = Math.max(svgRect.width * scale, 800);
  const height = Math.max(svgRect.height * scale, 400);

  const img = new Image();
  img.crossOrigin = "anonymous";

  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("Failed to load SVG for PNG export"));
    img.src = svgUrl;
  });

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(img, 0, 0, width, height);

  URL.revokeObjectURL(svgUrl);

  const pngBlob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob((b) => resolve(b), "image/png"),
  );
  if (!pngBlob) throw new Error("Failed to create PNG blob");

  const pngUrl = URL.createObjectURL(pngBlob);
  const a = document.createElement("a");
  a.href = pngUrl;
  a.download = filename.endsWith(".png") ? filename : `${filename}.png`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(pngUrl), 100);
}
