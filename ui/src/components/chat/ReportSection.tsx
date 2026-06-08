import ReactMarkdown from "react-markdown";
import { BookOpen, Database, Cpu, FlaskConical, Lightbulb, AlertTriangle } from "lucide-react";
import { Collapsible } from "@/components/shared/Collapsible";
import type { ReportSections } from "@/lib/store";

const titles: Record<keyof ReportSections, string> = {
  literature_review: "Literature Review",
  datasets: "Datasets",
  models: "Models",
  evaluation_plan: "Evaluation Plan",
  prototype_guidance: "Prototype Guidance",
};

const sectionIcons: Record<keyof ReportSections, React.ReactNode> = {
  literature_review: <BookOpen className="h-3.5 w-3.5" />,
  datasets: <Database className="h-3.5 w-3.5" />,
  models: <Cpu className="h-3.5 w-3.5" />,
  evaluation_plan: <FlaskConical className="h-3.5 w-3.5" />,
  prototype_guidance: <Lightbulb className="h-3.5 w-3.5" />,
};

function parseSection(raw: unknown): unknown {
  if (typeof raw === "object" && raw !== null) return raw;
  if (typeof raw === "string") {
    const trimmed = raw.trim();
    if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (typeof parsed === "object" && parsed !== null) return parsed;
      } catch {}
    }
    return raw;
  }
  return raw;
}

function getCardTitle(paper: Record<string, unknown>): string {
  const titleKeys = [
    "title",
    "name",
    "component",
    "component_name",
    "label",
    "step",
    "step_name",
    "phase",
    "phase_name",
    "module",
    "module_name",
    "metric",
    "metric_name",
  ] as const;

  for (const key of titleKeys) {
    const value = paper[key];
    if (typeof value === "string" && value.trim()) return value;
  }

  return "Untitled";
}

function PaperCard({ paper }: { paper: Record<string, unknown> }) {
  const title = getCardTitle(paper);
  const authors = Array.isArray(paper.authors)
    ? paper.authors.join(", ")
    : typeof paper.authors === "string" ? paper.authors : "";
  const year = paper.year ? String(paper.year) : "";
  const relevance = String(paper.relevance || paper.description || "");
  const purpose = String(paper.purpose || "");
  const split = paper.split as Record<string, number> | undefined;

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 flex flex-col gap-1.5 hover:bg-surface-hover/40 transition-colors">
      <h4 className="text-sm font-medium text-foreground leading-snug">{title}</h4>
      <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
        {authors && <span>{authors}</span>}
        {year && (
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary font-medium">
            {year}
          </span>
        )}
        {paper.type && (
          <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-blue-400 font-medium">
            {String(paper.type)}
          </span>
        )}
      </div>
      {relevance && (
        <p className="text-xs text-text-secondary leading-relaxed mt-0.5">{relevance}</p>
      )}
      {purpose && (
        <p className="text-xs text-text-muted leading-relaxed italic">{purpose}</p>
      )}
      {split && typeof split === "object" && (
        <div className="flex gap-3 text-[10px] text-text-muted mt-0.5">
          {Object.entries(split).map(([k, v]) => (
            <span key={k}>
              <span className="font-medium text-text-secondary">{k}</span>: {String(v)}
            </span>
          ))}
        </div>
      )}
      {Array.isArray(paper.pros) && paper.pros.length > 0 && (
        <div className="mt-1">
          <span className="text-[10px] font-medium text-green-400 uppercase tracking-wider">Pros</span>
          <ul className="mt-0.5 space-y-0.5">
            {paper.pros.map((p: string, i: number) => (
              <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                <span className="text-green-400 mt-0.5">+</span> {p}
              </li>
            ))}
          </ul>
        </div>
      )}
      {Array.isArray(paper.cons) && paper.cons.length > 0 && (
        <div className="mt-1">
          <span className="text-[10px] font-medium text-red-400 uppercase tracking-wider">Cons</span>
          <ul className="mt-0.5 space-y-0.5">
            {paper.cons.map((c: string, i: number) => (
              <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                <span className="text-red-400 mt-0.5">-</span> {c}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ArraySection({ label, items }: { label: string; items: unknown[] }) {
  if (items.length === 0) return null;
  const allObjects = items.every((item) => typeof item === "object" && item !== null);

  return (
    <div>
      <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium mb-2">
        {label.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
        <span className="ml-1.5 text-text-secondary">({items.length})</span>
      </h4>
      <div className="flex flex-col gap-2">
        {allObjects
          ? items.map((item, i) => <PaperCard key={i} paper={item as Record<string, unknown>} />)
          : items.map((item, i) => (
              <div key={i} className="text-xs text-text-secondary bg-surface/50 rounded-md px-3 py-1.5">
                {typeof item === "string" ? item : JSON.stringify(item)}
              </div>
            ))
        }
      </div>
    </div>
  );
}

function TextSection({ label, value }: { label: string; value: string }) {
  const words = value.split(/\s+/).length;
  const isLong = words > 40;

  return (
    <Collapsible title={label.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())} defaultOpen={!isLong}>
      <div className="text-xs text-text-secondary leading-relaxed">
        <ReactMarkdown>{value}</ReactMarkdown>
      </div>
    </Collapsible>
  );
}

function ParsedSectionContent({ data }: { data: unknown }) {
  if (Array.isArray(data)) {
    return <ArraySection label="Items" items={data} />;
  }

  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;

    if (Array.isArray(obj.papers) && obj.papers.length > 0) {
      const keyConcepts = obj.key_concepts as Record<string, unknown> | undefined;

      return (
        <div className="flex flex-col gap-3">
          <ArraySection label="Papers" items={obj.papers} />

          {keyConcepts && typeof keyConcepts === "object" && (
            <div>
              <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium mb-2">
                Key Concepts
              </h4>
              <div className="flex flex-col gap-2">
                {Object.entries(keyConcepts).map(([k, v]) => (
                  <Collapsible key={k} title={k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())} defaultOpen>
                    <div className="text-xs text-text-secondary leading-relaxed">
                      <ReactMarkdown>{typeof v === "string" ? v : JSON.stringify(v, null, 2)}</ReactMarkdown>
                    </div>
                  </Collapsible>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    const entries = Object.entries(obj);
    if (entries.length > 0) {
      return (
        <div className="flex flex-col gap-2">
          {entries.map(([k, v]) => (
            <div key={k}>
              {Array.isArray(v) ? (
                <ArraySection label={k} items={v} />
              ) : typeof v === "object" && v !== null ? (
                <Collapsible title={k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())} defaultOpen>
                  <div className="text-xs text-text-secondary leading-relaxed">
                    <ReactMarkdown>{JSON.stringify(v, null, 2)}</ReactMarkdown>
                  </div>
                </Collapsible>
              ) : (
                <div className="rounded-lg border border-border bg-surface/30 p-2.5">
                  <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">
                    {k.replace(/_/g, " ")}
                  </span>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">{String(v)}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }
  }

  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  return (
    <div className="md-body">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}

function ErrorReport({ report }: { report: Record<string, unknown> }) {
  const message = String(report.message || "Unknown error");
  const topics = Array.isArray(report.supported_topics) ? report.supported_topics : [];

  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-medium text-amber-300">Not a research query</span>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed mb-3">{message}</p>
      {topics.length > 0 && (
        <div>
          <p className="text-[11px] uppercase tracking-wider text-text-muted font-medium mb-1.5">
            Supported topics
          </p>
          <ul className="flex flex-wrap gap-1.5">
            {topics.map((topic, i) => (
              <span
                key={i}
                className="rounded-full border border-border bg-background px-2 py-0.5 text-[11px] text-text-secondary"
              >
                {String(topic)}
              </span>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function ReportSections({ sections }: { sections: ReportSections }) {
  const raw = sections as Record<string, unknown>;

  if (raw?.error === "not_research_query") {
    return <ErrorReport report={raw} />;
  }

  const keys = Object.keys(titles) as (keyof ReportSections)[];
  return (
    <div className="flex flex-col gap-2">
      {keys.map((k, i) => {
        const value = sections[k];
        const data = parseSection(value);
        return (
          <Collapsible key={k} title={titles[k]} defaultOpen={i === 0} badge={sectionIcons[k]}>
            {data != null && data !== "" ? (
              <ParsedSectionContent data={data} />
            ) : (
              <p className="text-sm text-text-muted italic">
                Not applicable for this query
              </p>
            )}
          </Collapsible>
        );
      })}
    </div>
  );
}
