import ReactMarkdown from "react-markdown";
import {
  BookOpen, Database, Cpu, FlaskConical, Lightbulb, AlertTriangle,
  Boxes, GitBranch, Layers, Library, Tag, Code2, Star, BarChart3, Calendar, Package,
} from "lucide-react";
import { Collapsible } from "@/components/shared/Collapsible";
import type {
  ReportSections, SectionValue, StructuredSection, SectionItem, PhaseEntry, PaperEntry,
} from "@/lib/store";

type SectionKey = "literature_review" | "datasets" | "models" | "evaluation_plan" | "prototype_guidance";

const titles: Record<SectionKey, string> = {
  literature_review: "Literature Review",
  datasets: "Datasets",
  models: "Models",
  evaluation_plan: "Evaluation Plan",
  prototype_guidance: "Prototype Guidance",
};

const sectionIcons: Record<SectionKey, React.ReactNode> = {
  literature_review: <BookOpen className="h-3.5 w-3.5" />,
  datasets: <Database className="h-3.5 w-3.5" />,
  models: <Cpu className="h-3.5 w-3.5" />,
  evaluation_plan: <FlaskConical className="h-3.5 w-3.5" />,
  prototype_guidance: <Lightbulb className="h-3.5 w-3.5" />,
};

// ── helpers ────────────────────────────────────────────────────────────────

function formatLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const titleKeys = [
  "title", "name", "component", "component_name", "label", "step", "step_name",
  "phase", "phase_name", "module", "module_name", "metric", "metric_name",
  "heading", "summary",
] as const;

function getCardTitle(item: Record<string, unknown>, fallback: string): string {
  for (const key of titleKeys) {
    const value = item[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  for (const value of Object.values(item)) {
    if (typeof value === "string" && value.trim()) return value;
  }
  return fallback;
}

function renderInlineValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

// Tech-stack keyword → icon + colour mapping for the top pill bar
const TECH_ICON_RULES: Array<[RegExp, { icon: React.ReactNode; tint: string }]> = [
  [/pytorch|torch|tensorflow|keras|jax|sklearn|scikit|numpy|pandas|scipy|polars/i,
    { icon: <Code2 className="h-3 w-3" />, tint: "bg-orange-500/10 text-orange-400 border-orange-500/20" }],
  [/lightfm|bert|gpt|llm|transformer|sasrec|lightgcn|pinsage|recurrent|gru|maml|prototypical|svd|instructrec|p5/i,
    { icon: <Cpu className="h-3 w-3" />, tint: "bg-blue-500/10 text-blue-400 border-blue-500/20" }],
  [/movielens|amazon|yelp|spotify|goodreads|igdb|steam|goodreads|netflix|bookcrossing|last\.?fm/i,
    { icon: <Database className="h-3 w-3" />, tint: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" }],
  [/faiss|annoy|hnsw|qdrant|weaviate|pinecone|milvus|redis|elasticsearch|cassandra/i,
    { icon: <Boxes className="h-3 w-3" />, tint: "bg-purple-500/10 text-purple-400 border-purple-500/20" }],
  [/mlflow|wandb|optuna|dvc|airflow|kubeflow|ray|tensorboard|hydra/i,
    { icon: <GitBranch className="h-3 w-3" />, tint: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" }],
  [/fastapi|flask|django|streamlit|docker|kubernetes|aws|gcp|azure|nginx|uvicorn|pydantic/i,
    { icon: <Library className="h-3 w-3" />, tint: "bg-amber-500/10 text-amber-400 border-amber-500/20" }],
  [/implicit|surprise|recbole|catboost|xgboost|lightgbm|prophet/i,
    { icon: <Layers className="h-3 w-3" />, tint: "bg-pink-500/10 text-pink-400 border-pink-500/20" }],
];

function techStyle(name: string): { icon: React.ReactNode; tint: string } {
  for (const [pat, style] of TECH_ICON_RULES) {
    if (pat.test(name)) return style;
  }
  return { icon: <Tag className="h-3 w-3" />, tint: "bg-surface text-text-secondary border-border" };
}

// ── tech stack bar ─────────────────────────────────────────────────────────

function TechStackBar({ items }: { items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="rounded-xl border border-border bg-surface/40 p-3">
      <div className="mb-2 flex items-center gap-2 text-[10px] font-medium uppercase tracking-wider text-text-muted">
        <Package className="h-3 w-3" />
        Tech Stack
        <span className="text-text-secondary">({items.length})</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => {
          const { icon, tint } = techStyle(item);
          return (
            <span
              key={`${item}-${i}`}
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium ${tint}`}
            >
              {icon}
              {item}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ── card primitives ────────────────────────────────────────────────────────

function PillList({ label, items, color = "default" }: { label: string; items: string[]; color?: "default" | "green" | "red" | "blue" }) {
  if (!items || items.length === 0) return null;
  const cls = {
    default: "bg-surface text-text-secondary border-border",
    green: "bg-green-500/10 text-green-400 border-green-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  }[color];
  return (
    <div className="mt-2">
      <div className="text-[10px] font-medium uppercase tracking-wider text-text-muted">{label}</div>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {items.map((it, i) => (
          <span key={i} className={`rounded-full border px-2 py-0.5 text-[11px] ${cls}`}>{it}</span>
        ))}
      </div>
    </div>
  );
}

function KeyValueList({ data, skipKeys = [] }: { data: Record<string, unknown>; skipKeys?: string[] }) {
  const entries = Object.entries(data).filter(
    ([k, v]) => !skipKeys.includes(k) && v != null && v !== "",
  );
  if (entries.length === 0) return null;
  return (
    <div className="mt-2 grid gap-2">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-md border border-border bg-background/40 p-2">
          <div className="text-[10px] font-medium uppercase tracking-wider text-text-muted">
            {formatLabel(key)}
          </div>
          {Array.isArray(value) ? (
            <div className="mt-1 flex flex-wrap gap-1.5">
              {value.map((item, index) => (
                <span
                  key={`${key}-${index}`}
                  className="rounded-full border border-border bg-surface px-2 py-0.5 text-[11px] text-text-secondary"
                >
                  {renderInlineValue(item)}
                </span>
              ))}
            </div>
          ) : isObject(value) ? (
            <div className="mt-1 grid gap-1">
              {Object.entries(value).map(([nestedKey, nestedValue]) => (
                <div key={nestedKey} className="text-xs text-text-secondary leading-relaxed">
                  <span className="font-medium text-foreground">{formatLabel(nestedKey)}:</span>{" "}
                  {renderInlineValue(nestedValue)}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-1 text-xs text-text-secondary leading-relaxed">{renderInlineValue(value)}</p>
          )}
        </div>
      ))}
    </div>
  );
}

// ── model card ─────────────────────────────────────────────────────────────

function ModelCard({ model, index }: { model: SectionItem; index: number }) {
  const name = String(model.name || `Model ${index + 1}`);
  const type = String(model.type || "");
  const purpose = String(model.purpose || model.description || "");
  const whenToUse = String(model.when_to_use || "");
  const libraries = Array.isArray(model.libraries) ? (model.libraries as string[]) : [];
  const pros = Array.isArray(model.pros) ? (model.pros as string[]) : [];
  const cons = Array.isArray(model.cons) ? (model.cons as string[]) : [];
  const skipForModel = ["name", "type", "purpose", "description", "libraries", "pros", "cons", "when_to_use"];
  const extra = Object.fromEntries(
    Object.entries(model).filter(([k, v]) => !skipForModel.includes(k) && v != null && v !== ""),
  );

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground leading-snug">{name}</h4>
        {type && (
          <span className="shrink-0 rounded-full bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 text-[10px] font-medium text-blue-400 capitalize">
            {type}
          </span>
        )}
      </div>
      {purpose && <p className="mt-1 text-xs text-text-secondary leading-relaxed">{purpose}</p>}
      {whenToUse && (
        <p className="mt-1 text-[11px] text-text-muted italic">Use when: {whenToUse}</p>
      )}
      {libraries.length > 0 && <PillList label="Libraries" items={libraries} color="blue" />}
      {pros.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase tracking-wider text-green-400">Pros</div>
          <ul className="mt-0.5 space-y-0.5">
            {pros.map((p, i) => (
              <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                <span className="text-green-400 mt-0.5">+</span> {p}
              </li>
            ))}
          </ul>
        </div>
      )}
      {cons.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase tracking-wider text-red-400">Cons</div>
          <ul className="mt-0.5 space-y-0.5">
            {cons.map((c, i) => (
              <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                <span className="text-red-400 mt-0.5">−</span> {c}
              </li>
            ))}
          </ul>
        </div>
      )}
      {Object.keys(extra).length > 0 && <KeyValueList data={extra} />}
    </div>
  );
}

// ── dataset card ───────────────────────────────────────────────────────────

function DatasetCard({ dataset, index }: { dataset: SectionItem; index: number }) {
  const name = String(dataset.name || `Dataset ${index + 1}`);
  const domain = String(dataset.domain || "");
  const size = String(dataset.size || "");
  const source = String(dataset.source || "");
  const license = String(dataset.license || "");
  const suitable = String(dataset.suitable_for || dataset.description || "");
  const url = String(dataset.url || "");

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground leading-snug">{name}</h4>
        {domain && (
          <span className="shrink-0 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-medium text-emerald-400 capitalize">
            {domain}
          </span>
        )}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-2 text-[11px] text-text-muted">
        {size && (
          <span className="inline-flex items-center gap-1">
            <BarChart3 className="h-3 w-3" /> {size}
          </span>
        )}
        {source && (
          <span className="inline-flex items-center gap-1">
            <Library className="h-3 w-3" /> {source}
          </span>
        )}
        {license && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-amber-400">
            {license}
          </span>
        )}
      </div>
      {suitable && <p className="mt-1.5 text-xs text-text-secondary leading-relaxed">{suitable}</p>}
      {url && (
        <a
          href={url}
          target="_blank"
          rel="noreferrer noopener"
          className="mt-1.5 inline-block text-[11px] text-primary hover:underline"
        >
          {url}
        </a>
      )}
    </div>
  );
}

// ── metric card ────────────────────────────────────────────────────────────

function MetricCard({ metric, index }: { metric: SectionItem; index: number }) {
  const name = String(metric.metric || metric.name || `Metric ${index + 1}`);
  const type = String(metric.type || "");
  const target = String(metric.target || metric.purpose || "");
  const calc = String(metric.calculation || metric.description || "");
  const threshold = String(metric.threshold_or_goal || "");

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground leading-snug">{name}</h4>
        {type && (
          <span className="shrink-0 rounded-full bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 text-[10px] font-medium text-cyan-400 capitalize">
            {type}
          </span>
        )}
      </div>
      {target && <p className="mt-1 text-[11px] text-text-muted">Target: {target}</p>}
      {calc && <p className="mt-1 text-xs text-text-secondary leading-relaxed">{calc}</p>}
      {threshold && (
        <div className="mt-1.5 inline-flex items-center gap-1 rounded-md border border-green-500/20 bg-green-500/10 px-2 py-0.5 text-[11px] text-green-400">
          <Star className="h-3 w-3" /> Goal: {threshold}
        </div>
      )}
    </div>
  );
}

// ── phase card ─────────────────────────────────────────────────────────────

function PhaseCard({ phase, index }: { phase: PhaseEntry; index: number }) {
  const name = String(phase.phase || `Phase ${index + 1}`);
  const weeks = String(phase.weeks || "");
  const goal = String(phase.goal || "");
  const tasks = Array.isArray(phase.tasks) ? (phase.tasks as string[]) : [];
  const tech = Array.isArray(phase.tech) ? (phase.tech as string[]) : [];
  const deliverable = String(phase.deliverable || "");

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground leading-snug">{name}</h4>
        {weeks && (
          <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 text-[10px] font-medium text-purple-400">
            <Calendar className="h-3 w-3" /> Week {weeks}
          </span>
        )}
      </div>
      {goal && <p className="mt-1 text-xs text-text-secondary leading-relaxed">{goal}</p>}
      {tasks.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Tasks</div>
          <ul className="mt-0.5 space-y-0.5">
            {tasks.map((t, i) => (
              <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                <span className="text-primary mt-0.5">▸</span> {t}
              </li>
            ))}
          </ul>
        </div>
      )}
      {tech.length > 0 && <PillList label="Tech" items={tech} color="blue" />}
      {deliverable && (
        <div className="mt-2 rounded-md border border-green-500/20 bg-green-500/5 px-2 py-1 text-[11px] text-green-400">
          <span className="font-medium">Deliverable:</span> {deliverable}
        </div>
      )}
    </div>
  );
}

// ── paper card (existing, extended with key_finding) ──────────────────────

function PaperCard({ paper, fallbackTitle }: { paper: PaperEntry; fallbackTitle: string }) {
  const title = getCardTitle(paper as unknown as Record<string, unknown>, fallbackTitle);
  const authors = Array.isArray(paper.authors) ? paper.authors.join(", ") : (paper.authors || "");
  const year = paper.year ? String(paper.year) : "";
  const keyFinding = String(paper.key_finding || paper.relevance || paper.description || "");
  const venue = String(paper.venue || "");
  const url = String(paper.url || "");
  const skip = ["title", "name", "authors", "year", "key_finding", "relevance", "description", "venue", "url"];
  const extra = Object.fromEntries(
    Object.entries(paper).filter(([k, v]) => !skip.includes(k) && v != null && v !== ""),
  );

  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <h4 className="text-sm font-medium text-foreground leading-snug">{title}</h4>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
        {authors && <span>{authors}</span>}
        {year && (
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary font-medium">{year}</span>
        )}
        {venue && <span className="italic">{venue}</span>}
      </div>
      {keyFinding && <p className="mt-1.5 text-xs text-text-secondary leading-relaxed">{keyFinding}</p>}
      {url && (
        <a href={url} target="_blank" rel="noreferrer noopener" className="mt-1 inline-block text-[11px] text-primary hover:underline">
          {url}
        </a>
      )}
      {Object.keys(extra).length > 0 && <KeyValueList data={extra} />}
    </div>
  );
}

// ── free-form text → lightweight item extractor (fallback) ─────────────────
//
// When the LLM returns a plain string (legacy mode, or text-only fallback),
// split into "items" by numbered list or bolded prefix. This keeps the UI
// informative even when structured output failed.

interface ExtractedItem {
  title: string;
  body: string;
}

function extractItemsFromText(text: string): ExtractedItem[] {
  if (!text) return [];
  // Strip markdown links/images but keep their text
  const cleaned = text
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

  const items: ExtractedItem[] = [];
  // Pattern A: "**Name**: rest of paragraph"
  const boldPrefix = cleaned.split(/\n(?=\s*\*\*[^*]+\*\*\s*[:\-–—])/);
  if (boldPrefix.length > 1) {
    for (const chunk of boldPrefix) {
      const m = chunk.match(/^\s*\*\*([^*]+)\*\*\s*[:\-–—]\s*([\s\S]*)$/);
      if (m) items.push({ title: m[1].trim(), body: m[2].trim() });
    }
    if (items.length > 0) return items;
  }
  // Pattern B: numbered list "1. **Name** — body" / "1. Name — body"
  const numbered = cleaned.split(/\n(?=\s*\d+[\.)]\s+)/);
  if (numbered.length > 1) {
    for (const chunk of numbered) {
      const m = chunk.match(/^\s*\d+[\.)]\s+(?:\*\*([^*]+)\*\*\s*[:\-–—]?\s*)?([\s\S]*)$/);
      if (m && (m[1] || m[2].trim())) {
        items.push({ title: (m[1] || m[2].split(/[.!?\n]/)[0] || `Item ${items.length + 1}`).trim().slice(0, 80), body: m[2].trim() });
      }
    }
    if (items.length > 0) return items;
  }
  return [];
}

function ExtractedItemCard({ item, index }: { item: ExtractedItem; index: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface/50 p-3 hover:bg-surface-hover/40 transition-colors">
      <h4 className="text-sm font-medium text-foreground leading-snug">{item.title}</h4>
      <p className="mt-1 text-xs text-text-secondary leading-relaxed">{item.body}</p>
    </div>
  );
}

// ── section-aware renderer ────────────────────────────────────────────────

function TextBlock({ text }: { text: string }) {
  if (!text || !text.trim()) return null;
  return (
    <div className="md-body text-xs text-text-secondary leading-relaxed">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}

interface CardSectionProps {
  sectionKey: SectionKey;
  data: StructuredSection;
}

function CardSection({ sectionKey, data }: CardSectionProps) {
  const { text, items = [], papers = [], phases = [], special_considerations, tech_stack_notes, key_concepts } = data;

  if (sectionKey === "literature_review") {
    return (
      <div className="flex flex-col gap-3">
        <TextBlock text={text || ""} />
        {papers.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">
              Papers <span className="ml-1 text-text-secondary">({papers.length})</span>
            </h4>
            {papers.map((p, i) => <PaperCard key={i} paper={p} fallbackTitle={`Paper ${i + 1}`} />)}
          </div>
        )}
        {key_concepts && isObject(key_concepts) && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">Key Concepts</h4>
            {Object.entries(key_concepts).map(([k, v]) =>
              isObject(v) ? (
                <Collapsible key={k} title={formatLabel(k)} defaultOpen>
                  <KeyValueList data={v as Record<string, unknown>} />
                </Collapsible>
              ) : (
                <Collapsible key={k} title={formatLabel(k)} defaultOpen>
                  <TextBlock text={typeof v === "string" ? v : JSON.stringify(v, null, 2)} />
                </Collapsible>
              ),
            )}
          </div>
        )}
      </div>
    );
  }

  if (sectionKey === "datasets") {
    return (
      <div className="flex flex-col gap-3">
        <TextBlock text={text || ""} />
        {items.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">
              Datasets <span className="ml-1 text-text-secondary">({items.length})</span>
            </h4>
            {items.map((d, i) => <DatasetCard key={i} dataset={d} index={i} />)}
          </div>
        )}
      </div>
    );
  }

  if (sectionKey === "models") {
    return (
      <div className="flex flex-col gap-3">
        <TextBlock text={text || ""} />
        {items.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">
              Models <span className="ml-1 text-text-secondary">({items.length})</span>
            </h4>
            {items.map((m, i) => <ModelCard key={i} model={m} index={i} />)}
          </div>
        )}
      </div>
    );
  }

  if (sectionKey === "evaluation_plan") {
    return (
      <div className="flex flex-col gap-3">
        <TextBlock text={text || ""} />
        {items.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">
              Metrics <span className="ml-1 text-text-secondary">({items.length})</span>
            </h4>
            {items.map((m, i) => <MetricCard key={i} metric={m} index={i} />)}
          </div>
        )}
        {Array.isArray(special_considerations) && special_considerations.length > 0 && (
          <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-2.5">
            <div className="text-[10px] font-medium uppercase tracking-wider text-amber-400">Special considerations</div>
            <ul className="mt-1 space-y-0.5">
              {special_considerations.map((s, i) => (
                <li key={i} className="text-xs text-text-secondary flex items-start gap-1.5">
                  <span className="text-amber-400 mt-0.5">⚠</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (sectionKey === "prototype_guidance") {
    return (
      <div className="flex flex-col gap-3">
        <TextBlock text={text || ""} />
        {phases.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium">
              Roadmap <span className="ml-1 text-text-secondary">({phases.length} phases)</span>
            </h4>
            {phases.map((p, i) => <PhaseCard key={i} phase={p} index={i} />)}
          </div>
        )}
        {Array.isArray(tech_stack_notes) && tech_stack_notes.length > 0 && (
          <div>
            <h4 className="text-[11px] uppercase tracking-wider text-text-muted font-medium mb-1.5">
              Tech stack notes
            </h4>
            <PillList label="" items={tech_stack_notes} color="blue" />
          </div>
        )}
      </div>
    );
  }

  return null;
}

function ParsedSectionContent({ data }: { data: SectionValue }) {
  if (data == null || data === "") {
    return <p className="text-sm text-text-muted italic">Not applicable for this query</p>;
  }

  if (typeof data === "string") {
    // Try to extract items from free-form text; fall back to plain markdown
    const items = extractItemsFromText(data);
    if (items.length >= 2) {
      return (
        <div className="flex flex-col gap-3">
          <TextBlock text={data} />
          <div className="flex flex-col gap-2">
            {items.map((it, i) => <ExtractedItemCard key={i} item={it} index={i} />)}
          </div>
        </div>
      );
    }
    return <TextBlock text={data} />;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <p className="text-sm text-text-muted italic">Not applicable for this query</p>;
    }
    return (
      <div className="flex flex-col gap-2">
        {data.map((item, i) => {
          if (isObject(item) && ("title" in item || "name" in item)) {
            return <PaperCard key={i} paper={item as PaperEntry} fallbackTitle={`Item ${i + 1}`} />;
          }
          return (
            <div key={i} className="rounded-md border border-border bg-surface/50 px-3 py-1.5 text-xs text-text-secondary">
              {typeof item === "string" ? item : JSON.stringify(item)}
            </div>
          );
        })}
      </div>
    );
  }

  if (isObject(data)) {
    // Generic object: render text field first, then key/value pairs
    const text = typeof data.text === "string" ? data.text : "";
    const knownKeys = new Set(["text", "papers", "items", "phases", "key_concepts", "special_considerations", "tech_stack_notes"]);
    const extra = Object.fromEntries(
      Object.entries(data).filter(([k, v]) => !knownKeys.has(k) && v != null && v !== ""),
    );
    return (
      <div className="flex flex-col gap-3">
        {text && <TextBlock text={text} />}
        {Object.keys(extra).length > 0 && <KeyValueList data={extra} />}
      </div>
    );
  }

  return null;
}

// ── error report ───────────────────────────────────────────────────────────

function ErrorReport({ report }: { report: Record<string, unknown> }) {
  const errorType = String(report.error || "");
  const message = String(report.message || "Unknown error");
  const reason = typeof report.reason === "string" ? report.reason : "";
  const suggestion = typeof report.suggestion === "string" ? report.suggestion : "";
  const topics = Array.isArray(report.supported_topics) ? (report.supported_topics as unknown[]) : [];
  const validation = report.validation && typeof report.validation === "object"
    ? (report.validation as Record<string, unknown>)
    : null;

  const isAgentUnavailable = errorType === "no_suitable_agent";
  const title = isAgentUnavailable ? "Agent unavailable" : "Not a research query";
  const borderColor = isAgentUnavailable ? "border-red-500/30" : "border-amber-500/30";
  const bgColor = isAgentUnavailable ? "bg-red-500/5" : "bg-amber-500/5";
  const iconColor = isAgentUnavailable ? "text-red-400" : "text-amber-400";
  const textColor = isAgentUnavailable ? "text-red-300" : "text-amber-300";

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} p-4`}>
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className={`h-4 w-4 ${iconColor}`} />
        <span className={`text-sm font-medium ${textColor}`}>{title}</span>
      </div>
      <p className="text-sm text-text-secondary leading-relaxed mb-3">{message}</p>
      {reason && <p className="mb-3 text-xs leading-relaxed text-text-muted">{reason}</p>}
      {suggestion && (
        <div className="mb-3 rounded-md border border-border bg-background/50 px-3 py-2 text-xs text-text-secondary">
          <span className="font-medium text-foreground">Suggestion:</span> {suggestion}
        </div>
      )}
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
      {validation && (
        <div className="mt-3">
          <p className="text-[11px] uppercase tracking-wider text-text-muted font-medium mb-1.5">
            Validation details
          </p>
          <div className="rounded-md border border-border bg-background/50 p-3 text-xs text-text-secondary">
            <KeyValueList data={validation} />
          </div>
        </div>
      )}
    </div>
  );
}

// ── top-level component ────────────────────────────────────────────────────

function parseSection(value: SectionValue): SectionValue {
  if (typeof value !== "string") return value;
  const trimmed = value.trim();
  if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (typeof parsed === "object" && parsed !== null) return parsed as SectionValue;
    } catch {
      // not JSON
    }
  }
  return value;
}

export function ReportSections({ sections }: { sections: ReportSections }) {
  const raw = sections as Record<string, unknown>;

  if (raw?.error === "not_research_query" || raw?.error === "no_suitable_agent") {
    return <ErrorReport report={raw} />;
  }

  const keys = Object.keys(titles) as SectionKey[];
  const techStack = Array.isArray(sections.tech_stack) ? sections.tech_stack : [];

  return (
    <div className="flex flex-col gap-2">
      <TechStackBar items={techStack} />
      {keys.map((k, i) => {
        const value = sections[k] as SectionValue;
        const data = parseSection(value);
        return (
          <Collapsible key={k} title={titles[k]} defaultOpen={i === 0} badge={sectionIcons[k] as unknown as string}>
            {isStructuredSection(data) ? (
              <CardSection sectionKey={k} data={data} />
            ) : (
              <ParsedSectionContent data={data} />
            )}
          </Collapsible>
        );
      })}
    </div>
  );
}

function isStructuredSection(value: SectionValue): value is StructuredSection {
  if (!isObject(value)) return false;
  const v = value as Record<string, unknown>;
  return "papers" in v || "items" in v || "phases" in v || "key_concepts" in v;
}
