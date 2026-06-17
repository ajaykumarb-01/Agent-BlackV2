import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ExternalLink,
  Github,
  ArrowUpRight,
  Zap,
  Brain,
  Cpu,
  Network,
  FlaskConical,
  BarChart3,
  Globe,
  Layers,
  Shield,
  Workflow,
  Sparkles,
  FileText,
  MessageSquare,
  Settings,
  Gauge,
  Rocket,
} from "lucide-react";

export const Route = createFileRoute("/about")({
  head: () => ({ meta: [{ title: "About · Agent Black" }] }),
  component: About,
});

const PROJECT_URL = "https://github.com/hareesh08/Agent-BlackV2";

const team = [
  {
    name: "Hareesh",
    github: "https://github.com/hareesh08",
    role: "Solution Agent · Host Agent · FastAPI Backend · DevOps",
  },
  {
    name: "Ajay Kumar",
    github: "https://github.com/Ajaybala05",
    role: "Research Agent · Host Agent",
  },
  {
    name: "Shylaja",
    github: "https://github.com/shylaja-uu",
    role: "Experimental Agent",
  },
];

const features = [
  {
    icon: Brain,
    title: "Research-Relevance Gate",
    desc: "Smart query validation rejects non-research questions with helpful suggestions and supported topics.",
  },
  {
    icon: Zap,
    title: "LLM-Driven Orchestration",
    desc: "Agent selection, task decomposition, and result aggregation powered by multi-provider LLMs.",
  },
  {
    icon: Network,
    title: "39 MCP Tools",
    desc: "13 tools per agent covering paper search, dataset discovery, model recommendation, and more.",
  },
  {
    icon: Workflow,
    title: "A2A Protocol",
    desc: "Agents communicate seamlessly via JSON-RPC 2.0 with standardized agent cards and task routing.",
  },
  {
    icon: Gauge,
    title: "SSE Streaming",
    desc: "Real-time task progress streaming so you never lose sight of what's happening.",
  },
  {
    icon: FileText,
    title: "Structured Reports",
    desc: "Unified reports with literature review, datasets, models, evaluation plans, and PDF export.",
  },
];

const pipelineSteps = [
  { step: "0", title: "Relevance Gate", desc: "Validates research intent", icon: Shield },
  { step: "1", title: "Agent Selection", desc: "LLM picks the right agents", icon: Brain },
  { step: "2", title: "Task Decomposition", desc: "Breaks into sub-tasks", icon: Layers },
  { step: "3", title: "Concurrent Dispatch", desc: "Parallel agent execution", icon: Zap },
  { step: "4", title: "Result Aggregation", desc: "LLM synthesizes output", icon: Sparkles },
];

const agents = [
  {
    name: "CV Research Agent",
    port: 8001,
    domain: "Computer Vision",
    icon: Globe,
    specs: [
      "Image Classification",
      "Object Detection",
      "Segmentation",
      "Vision Transformers",
      "Medical Imaging",
      "Video Analytics",
    ],
  },
  {
    name: "NLP Solution Agent",
    port: 8002,
    domain: "NLP / Solution Architecture",
    icon: MessageSquare,
    specs: [
      "LLMs & RAG",
      "Prompt Engineering",
      "Text Classification",
      "Summarization",
      "Conversational AI",
      "Information Extraction",
    ],
  },
  {
    name: "ML Experiment Agent",
    port: 8003,
    domain: "Machine Learning Experiments",
    icon: FlaskConical,
    specs: [
      "Classical ML",
      "Feature Engineering",
      "Hyperparameter Tuning",
      "Time Series",
      "Experiment Design",
      "Model Explainability",
    ],
  },
];

const stack = [
  {
    category: "Frontend",
    items: [
      { name: "React 19", icon: "react", desc: "UI library" },
      { name: "TanStack Start", icon: "router", desc: "SSR + file-based routing" },
      { name: "Tailwind CSS v4", icon: "tailwind", desc: "Utility-first CSS" },
      { name: "shadcn/ui", icon: "ui", desc: "Component primitives" },
      { name: "Zustand", icon: "zustand", desc: "Persisted state" },
      { name: "TanStack Query", icon: "query", desc: "Data fetching + caching" },
      { name: "Mermaid.js", icon: "mermaid", desc: "Diagram rendering" },
      { name: "Vite 7", icon: "vite", desc: "Build tool" },
    ],
  },
  {
    category: "Backend",
    items: [
      { name: "FastAPI", icon: "fastapi", desc: "Async Python API" },
      { name: "Uvicorn", icon: "uvicorn", desc: "ASGI server" },
      { name: "Pydantic v2", icon: "pydantic", desc: "Data validation" },
      { name: "SQLite", icon: "sqlite", desc: "Config & history (WAL mode)" },
      { name: "HTTPX", icon: "httpx", desc: "Async HTTP client" },
    ],
  },
  {
    category: "Agents & Protocols",
    items: [
      { name: "MCP (JSON-RPC 2.0)", icon: "mcp", desc: "39 tools across 3 agents" },
      { name: "A2A Protocol", icon: "a2a", desc: "Agent-to-Agent communication" },
      { name: "SSE Streaming", icon: "sse", desc: "Real-time task progress" },
      { name: "Academic APIs", icon: "book", desc: "CrossRef + Semantic Scholar + arXiv" },
    ],
  },
  {
    category: "LLM Providers",
    items: [
      { name: "Google Gemini", icon: "gemini", desc: "gemini-1.5-flash default" },
      { name: "OpenAI", icon: "openai", desc: "gpt-4o" },
      { name: "Anthropic", icon: "anthropic", desc: "claude-3-5-sonnet" },
      { name: "Auto-Retry", icon: "retry", desc: "Automatic retry on failure" },
    ],
  },
];

function TechIcon({ icon }: { icon: string }) {
  const icons: Record<string, JSX.Element> = {
    react: (
      <svg viewBox="-11.5 -10.23174 23 20.46348" className="h-5 w-5" fill="currentColor">
        <circle cx="0" cy="0" r="2.05" />
        <g strokeWidth="1">
          <ellipse rx="11" ry="4.2" />
          <ellipse rx="11" ry="4.2" transform="rotate(60)" />
          <ellipse rx="11" ry="4.2" transform="rotate(120)" />
        </g>
      </svg>
    ),
    router: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2v4m0 12v4M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
      </svg>
    ),
    tailwind: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 6c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.3.74 1.9 1.35.98 1 2.13 2.15 4.6 2.15 2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.3-.74-1.9-1.35C15.02 7.15 13.87 6 12 6zM7 12c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.3.74 1.9 1.35C8.38 16.85 9.53 18 12 18c2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.3-.74-1.9-1.35C10.02 13.15 8.87 12 7 12z" />
      </svg>
    ),
    ui: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <rect x="3" y="3" width="7" height="7" />
        <rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" />
      </svg>
    ),
    zustand: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
    query: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 12h2l3-9 4 18 3-9h4" />
      </svg>
    ),
    vite: (
      <svg viewBox="0 0 256 257" className="h-5 w-5" fill="currentColor">
        <path d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.875 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 002.322-.004l117.867-21.483c5.438-.991 9.574 4.796 6.877 9.62z" />
        <path d="M185.432.063L96.44 17.501a3.268 3.268 0 00-2.634 3.014l-5.474 92.456a3.268 3.268 0 003.997 3.378l24.777-5.718c2.318-.535 4.413 1.507 3.936 3.838l-7.361 36.047c-.495 2.426 1.782 4.5 4.151 3.78l15.304-4.649c2.372-.72 4.652 1.36 4.15 3.788l-11.698 56.621c-.732 3.542 3.979 5.473 5.943 2.437l1.313-2.028l72.516-144.72c1.215-2.423-.88-5.186-3.54-4.672l-25.505 4.922c-2.396.462-4.435-1.77-3.759-4.114l16.646-57.705c.677-2.35-1.37-4.583-3.769-4.113z" />
      </svg>
    ),
    mermaid: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M22 3.5a1.5 1.5 0 00-3 0v3a1.5 1.5 0 003 0v-3zM16.5 18a1.5 1.5 0 00-3 0v3a1.5 1.5 0 003 0v-3zM5 6.5A1.5 1.5 0 003.5 5v-3a1.5 1.5 0 00-3 0v3A1.5 1.5 0 005 6.5zm0 11A1.5 1.5 0 003.5 16v3a1.5 1.5 0 003 0v-3zM5 6.5h6V2H5a3 3 0 00-3 3v1.5a3 3 0 003 3zm6 0h6.5a1.5 1.5 0 001.5-1.5V2h-8v4.5zm0 0v5H5a3 3 0 00-3 3V13a3 3 0 003 3h6v-6.5zm0 11h6.5a1.5 1.5 0 001.5-1.5V16H11v4.5z" />
      </svg>
    ),
    fastapi: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
    ),
    sqlite: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2C6.477 2 2 3.79 2 6v12c0 2.21 4.477 4 10 4s10-1.79 10-4V6c0-2.21-4.477-4-10-4zm0 2c4.963 0 8 1.79 8 2s-3.037 2-8 2-8-1.79-8-2 3.037-2 8-2zM4 10c0 .21 3.037 2 8 2s8-1.79 8-2v2c0 .21-3.037 2-8 2s-8-1.79-8-2v-2zm0 6c0 .21 3.037 2 8 2s8-1.79 8-2v2c0 .21-3.037 2-8 2s-8-1.79-8-2v-2z" />
      </svg>
    ),
    pydantic: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M2.5 12a1.5 1.5 0 011.5-1.5h2a1.5 1.5 0 010 3h-2a1.5 1.5 0 01-1.5-1.5zm7.5-1.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm5-3a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm-2.5 9a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM17 8a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM8.5 6.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3zm7 7a1.5 1.5 0 100 3 1.5 1.5 0 000-3z" />
      </svg>
    ),
    uvicorn: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-5a1 1 0 112 0 1 1 0 01-2 0zm-3.5-4a1 1 0 112 0 1 1 0 01-2 0zm7 0a1 1 0 112 0 1 1 0 01-2 0z" />
      </svg>
    ),
    mcp: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6zM7 7h0v2H5V7H3v2H1V5h2V3h2v2h2v2zm10 0h0v2h-2V7h-2V5h2V3h2v2h2v2h-2v2zm-10 6h0v2H5v-2H3v2H1v-4h2v-2h2v2h2v2zm10 0h0v2h-2v-2h-2v-2h2V9h2v2h2v4h-2v-2h-2v2z" />
      </svg>
    ),
    a2a: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M17 1l4 4-4 4" />
        <path d="M3 11V9a4 4 0 014-4h14" />
        <path d="M7 23l-4-4 4-4" />
        <path d="M21 13v2a4 4 0 01-4 4H3" />
      </svg>
    ),
    openai: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M22.282 9.821a5.985 5.985 0 00-.516-4.91 6.046 6.046 0 00-6.51-2.9A6.065 6.065 0 0014.98 2.06a5.985 5.985 0 00-3.998 2.9 6.046 6.046 0 00.743 7.097 5.98 5.98 0 00.51 4.911 6.051 6.051 0 006.515 2.9A5.985 5.985 0 0013.26 24a6.056 6.056 0 005.772-4.206 5.99 5.99 0 003.997-2.9 6.056 6.056 0 00-.747-7.073zM13.26 22.43a4.476 4.476 0 01-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 00.396-.681v-6.737l2.02 1.168a.071.071 0 01.038.052v5.583a4.504 4.504 0 01-4.494 4.494zM3.6 18.304a4.47 4.47 0 01-.535-3.014l.142.085 4.783 2.759a.771.771 0 00.78 0l5.843-3.369v2.332a.08.08 0 01-.033.062L9.74 19.95a4.5 4.5 0 01-6.14-1.646zM2.34 7.896a4.485 4.485 0 012.366-1.973V11.6a.766.766 0 00.388.676l5.815 3.355-2.02 1.168a.076.076 0 01-.071 0l-4.83-2.786A4.504 4.504 0 012.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 01.071 0l4.83 2.791a4.494 4.494 0 01-.676 8.105v-5.678a.79.79 0 00-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 00-.785 0L9.409 9.23V6.897a.066.066 0 01.028-.061l4.83-2.787a4.5 4.5 0 016.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 01-.038-.057V6.075a4.5 4.5 0 017.375-3.453l-.142.08L8.704 5.46a.795.795 0 00-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z" />
      </svg>
    ),
    sse: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 12h2l3-9 4 18 3-9h4" />
      </svg>
    ),
    gemini: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
    anthropic: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2L2 12l10 10 10-10L12 2zm0 4l6 6-6 6-6-6 6-6z" />
      </svg>
    ),
    retry: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12a9 9 0 11-6.22-8.56" />
        <path d="M21 3v5h-5" />
      </svg>
    ),
    book: (
      <svg
        viewBox="0 0 24 24"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
      </svg>
    ),
  };
  return icons[icon] || <div className="h-5 w-5 rounded bg-text-muted/30" />;
}

function About() {
  return (
    <div className="mx-auto w-full max-w-[960px] px-3 py-6 sm:px-4 sm:py-10">
      {/* Hero */}
      <div className="relative mb-14 overflow-hidden rounded-2xl border border-border bg-surface p-6 sm:p-10">
        <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-foreground/5 blur-3xl animate-pulse" />
        <div className="absolute -bottom-16 -left-16 h-56 w-56 rounded-full bg-foreground/3 blur-2xl animate-pulse [animation-delay:1s]" />
        <div className="absolute right-1/3 bottom-1/4 h-40 w-40 rounded-full bg-foreground/5 blur-3xl animate-pulse [animation-delay:2s]" />

        <div className="relative">
          <div className="mb-5 flex items-center gap-4">
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-foreground shadow-lg shadow-foreground/20">
              <span className="text-xl font-black text-background tracking-tighter">A·B</span>
              <div className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-background border border-border text-[10px] font-bold text-foreground shadow">
                v2
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Agent Black</h1>
              <p className="text-sm text-text-secondary">Multi-Agent AI Research Platform</p>
            </div>
          </div>

          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-text-secondary sm:text-base">
            A multi-agent system where a <strong className="text-foreground">Control Panel</strong>{" "}
            orchestrates three{" "}
            <strong className="text-foreground">specialized research agents</strong> to solve
            AI/ML/CV/NLP queries. Each agent is an independent FastAPI service with its own MCP tool
            server and A2A endpoint — delivering structured, end-to-end research workflows.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href={PROJECT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-foreground px-5 py-2.5 text-sm font-medium text-background hover:opacity-90 transition-opacity shadow-md shadow-foreground/10"
            >
              <Github className="h-4 w-4" />
              View on GitHub
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-hover px-5 py-2.5 text-sm font-medium hover:bg-surface-hover/80 transition-colors"
            >
              <BarChart3 className="h-4 w-4" />
              Open Dashboard
            </Link>
            <Link
              to="/"
              search={{ new: "1" }}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-hover px-5 py-2.5 text-sm font-medium hover:bg-surface-hover/80 transition-colors"
            >
              <MessageSquare className="h-4 w-4" />
              Start Query
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mb-14 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Agents", value: "3", sub: "CV · NLP · ML", icon: Cpu },
          { label: "MCP Tools", value: "39", sub: "13 per agent", icon: Network },
          { label: "Pipeline Steps", value: "5", sub: "End-to-end", icon: Workflow },
          {
            label: "LLM Providers",
            value: "3",
            sub: "Gemini · OpenAI · Anthropic",
            icon: Brain,
          },
        ].map((s) => (
          <div
            key={s.label}
            className="group relative rounded-xl border border-border bg-surface p-4 transition-all hover:border-foreground/20 hover:shadow-md overflow-hidden"
          >
            <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-foreground/5 blur-xl transition-opacity group-hover:bg-foreground/10" />
            <div className="relative">
              <div className="mb-2 flex items-center gap-2">
                <s.icon className="h-3.5 w-3.5 text-foreground" />
                <span className="text-[10px] uppercase tracking-wider text-text-muted font-medium">
                  {s.label}
                </span>
              </div>
              <div className="text-2xl font-black tracking-tight text-foreground">{s.value}</div>
              <p className="mt-0.5 text-[11px] text-text-muted">{s.sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Features */}
      <section className="mb-14">
        <div className="mb-6">
          <h2 className="text-lg font-bold tracking-tight">Key Features</h2>
          <p className="mt-1 text-sm text-text-secondary">What makes Agent Black powerful.</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="group relative rounded-xl border border-border bg-surface p-5 transition-all hover:border-foreground/20 hover:shadow-md"
            >
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-foreground/5 transition-transform group-hover:scale-110">
                <f.icon className="h-5 w-5 text-foreground" />
              </div>
              <h3 className="text-sm font-semibold">{f.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-text-secondary">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Orchestrator Pipeline */}
      <section className="mb-14">
        <div className="mb-6">
          <h2 className="text-lg font-bold tracking-tight">Orchestrator Pipeline</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Every query flows through 5 intelligent steps.
          </p>
        </div>

        <div className="relative rounded-xl border border-border bg-surface p-6">
          <div className="absolute left-[29px] top-10 bottom-10 w-px bg-border sm:left-1/2 sm:translate-x-px" />

          <div className="space-y-6">
            {pipelineSteps.map((s, i) => (
              <div
                key={s.step}
                className={`relative flex items-start gap-4 sm:gap-6 ${i % 2 === 1 ? "sm:flex-row-reverse" : ""}`}
              >
                <div className="relative z-10 flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border-2 border-border bg-background shadow-sm">
                  <s.icon className="h-5 w-5 text-foreground" />
                </div>
                <div
                  className={`flex-1 rounded-xl border border-border bg-background/50 p-4 ${i % 2 === 1 ? "sm:text-right" : ""}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded bg-foreground/10 text-[10px] font-bold text-foreground">
                      {s.step}
                    </span>
                    <h3 className="text-sm font-semibold">{s.title}</h3>
                  </div>
                  <p className="mt-1 text-xs text-text-secondary">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agents */}
      <section className="mb-14">
        <div className="mb-6">
          <h2 className="text-lg font-bold tracking-tight">Specialist Agents</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Each agent is a standalone FastAPI service with its own MCP tools and A2A endpoint.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {agents.map((a) => (
            <div
              key={a.name}
              className="group relative rounded-xl border border-border bg-surface p-5 transition-all hover:border-foreground/20 hover:shadow-lg"
            >
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-foreground/5 shadow-sm">
                  <a.icon className="h-5 w-5 text-foreground" />
                </div>
                <div>
                  <h3 className="text-sm font-bold">{a.name}</h3>
                  <p className="text-[11px] text-text-muted">
                    Port {a.port} · {a.domain}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {a.specs.map((s) => (
                  <span
                    key={s}
                    className="inline-flex items-center rounded-md border border-border bg-background px-2 py-0.5 text-[10px] font-medium text-text-secondary"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Team */}
      <section className="mb-14">
        <div className="mb-6">
          <h2 className="text-lg font-bold tracking-tight">Team</h2>
          <p className="mt-1 text-sm text-text-secondary">The people behind Agent Black.</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          {team.map((m, i) => (
            <a
              key={`${m.github}-${i}`}
              href={m.github}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative rounded-xl border border-border bg-surface p-5 transition-all hover:border-foreground/20 hover:shadow-lg"
            >
              <div className="mb-3 flex items-center gap-3">
                <div className="relative">
                  <img
                    src={`https://avatars.githubusercontent.com/${m.github.replace("https://github.com/", "")}`}
                    alt={m.name}
                    className="h-12 w-12 rounded-full border-2 border-border object-cover shadow-sm"
                    loading="lazy"
                  />
                  <div className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-surface bg-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-bold group-hover:underline">{m.name}</div>
                  <div className="flex items-center gap-1 text-[11px] text-text-muted">
                    <Github className="h-3 w-3" />
                    {m.github.replace("https://github.com/", "")}
                  </div>
                </div>
              </div>
              <p className="text-xs leading-relaxed text-text-secondary">{m.role}</p>
              <ExternalLink className="absolute right-3 top-3 h-3.5 w-3.5 text-text-muted opacity-0 transition-opacity group-hover:opacity-100" />
            </a>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="mb-14">
        <div className="mb-6">
          <h2 className="text-lg font-bold tracking-tight">Tech Stack</h2>
          <p className="mt-1 text-sm text-text-secondary">Technologies powering the platform.</p>
        </div>

        <div className="space-y-4">
          {stack.map((group) => (
            <div
              key={group.category}
              className="rounded-xl border border-border bg-surface overflow-hidden"
            >
              <div className="border-b border-border-light bg-foreground/[0.02] px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-text-muted">
                {group.category}
              </div>
              <div className="grid grid-cols-1 divide-y divide-border-light sm:grid-cols-2 sm:divide-x sm:divide-y-0">
                {group.items.map((item) => (
                  <div
                    key={item.name}
                    className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-foreground/[0.02]"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-foreground">
                      <TechIcon icon={item.icon} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium">{item.name}</div>
                      <div className="text-[11px] text-text-muted">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Links */}
      <section className="mb-14">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2">
              <Rocket className="h-4 w-4 text-foreground" />
              <h3 className="text-sm font-bold">Quick Start</h3>
            </div>
            <div className="space-y-2 text-xs text-text-secondary">
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded bg-foreground/10 text-[9px] font-bold text-foreground">
                  1
                </span>
                <code className="font-mono text-[11px]">pip install -r requirements.txt</code>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded bg-foreground/10 text-[9px] font-bold text-foreground">
                  2
                </span>
                <code className="font-mono text-[11px]">python start.py</code>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded bg-foreground/10 text-[9px] font-bold text-foreground">
                  3
                </span>
                <code className="font-mono text-[11px]">cd ui && bun install && bun run dev</code>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2">
              <Settings className="h-4 w-4 text-foreground" />
              <h3 className="text-sm font-bold">Service Ports</h3>
            </div>
            <div className="space-y-2 text-xs">
              {[
                { name: "Control Panel", port: "8000" },
                { name: "CV Agent", port: "8001" },
                { name: "NLP Agent", port: "8002" },
                { name: "ML Agent", port: "8003" },
                { name: "Frontend", port: "8080" },
              ].map((s) => (
                <div key={s.port} className="flex items-center justify-between">
                  <span className="text-text-secondary">{s.name}</span>
                  <span className="flex items-center gap-1.5 font-mono text-[11px]">
                    <span className="h-1.5 w-1.5 rounded-full bg-foreground" />:{s.port}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <div className="border-t border-border pt-6 text-center text-xs text-text-muted">
        <div className="flex items-center justify-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-foreground">
            <span className="text-[8px] font-bold text-background">A·B</span>
          </div>
          <p className="font-medium">Agent Black · Built with FastAPI, React, and Tailwind CSS</p>
        </div>
        <p className="mt-1">
          © {new Date().getFullYear()} Agent Black Contributors ·{" "}
          <a
            href={PROJECT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-foreground transition-colors"
          >
            MIT License
          </a>
        </p>
      </div>
    </div>
  );
}
