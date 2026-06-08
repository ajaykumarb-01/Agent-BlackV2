import { createFileRoute, Link } from "@tanstack/react-router";
import { ExternalLink, Github, ArrowUpRight } from "lucide-react";

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
    color: "#7B68EE",
  },
  {
    name: "Ajay Kumar",
    github: "https://github.com/Ajaybala05",
    role: "Research Agent · Host Agent",
    color: "#2ECC71",
  },
  {
    name: "Shylaja",
    github: "https://github.com/shylaja-uu",
    role: "Experimental Agent",
    color: "#E74C3C",
  },
];

const stack = [
  {
    category: "Frontend",
    items: [
      { name: "React 19", icon: "react", desc: "UI library" },
      { name: "TanStack Router", icon: "router", desc: "File-based routing" },
      { name: "Tailwind CSS v4", icon: "tailwind", desc: "Utility-first CSS" },
      { name: "Zustand", icon: "zustand", desc: "State management" },
      { name: "Vite 7", icon: "vite", desc: "Build tool" },
      { name: "Mermaid", icon: "mermaid", desc: "Diagram rendering" },
    ],
  },
  {
    category: "Backend",
    items: [
      { name: "FastAPI", icon: "fastapi", desc: "Async Python API" },
      { name: "SQLite", icon: "sqlite", desc: "Config & history store" },
      { name: "Pydantic", icon: "pydantic", desc: "Data validation" },
      { name: "Uvicorn", icon: "uvicorn", desc: "ASGI server" },
    ],
  },
  {
    category: "Agents & Protocols",
    items: [
      { name: "MCP", icon: "mcp", desc: "Model Context Protocol — 39 tools" },
      { name: "A2A", icon: "a2a", desc: "Agent-to-Agent JSON-RPC 2.0" },
      { name: "OpenAI API", icon: "openai", desc: "LLM provider (mimo-v2.5)" },
      { name: "SSE Streaming", icon: "sse", desc: "Real-time task progress" },
    ],
  },
  {
    category: "DevOps & Infra",
    items: [
      { name: "Python 3.12", icon: "python", desc: "Agent runtime" },
      { name: "Node.js", icon: "node", desc: "Frontend runtime" },
      { name: "HTTPX", icon: "httpx", desc: "Async HTTP client" },
      { name: "Importlib", icon: "importlib", desc: "Dynamic module loading" },
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
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v4m0 12v4M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
      </svg>
    ),
    tailwind: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 6c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.3.74 1.9 1.35.98 1 2.13 2.15 4.6 2.15 2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.3-.74-1.9-1.35C15.02 7.15 13.87 6 12 6zM7 12c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.3.74 1.9 1.35C8.38 16.85 9.53 18 12 18c2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.3-.74-1.9-1.35C10.02 13.15 8.87 12 7 12z" />
      </svg>
    ),
    zustand: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
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
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 12h2l3-9 4 18 3-9h4" />
      </svg>
    ),
    python: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.89.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z" />
      </svg>
    ),
    node: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
        <path d="M11.998 24c-.321 0-.636-.084-.914-.243l-2.894-1.682c-.438-.245-.225-.332-.08-.383.585-.203.703-.25 1.328-.604.065-.037.151-.023.218.017l2.246 1.325c.082.045.197.045.272 0l8.795-5.065c.082-.047.134-.141.134-.238V6.921c0-.099-.053-.192-.137-.242l-8.791-5.055c-.081-.047-.189-.047-.271 0L3.075 6.68c-.084.05-.137.143-.137.241v10.15c0 .097.054.189.135.235l2.409 1.392c1.307.654 2.108-.116 2.108-.89V7.787c0-.142.114-.253.256-.253h1.115c.139 0 .255.112.255.253v10.021c0 1.745-.95 2.745-2.604 2.745-.508 0-.909 0-2.026-.551L2.28 18.675A1.857 1.857 0 011 17.072V6.921c0-.682.363-1.316.953-1.666L10.744.19a1.926 1.926 0 011.816 0l8.794 5.065c.59.35.953.984.953 1.666v10.15c0 .681-.363 1.315-.953 1.665l-8.794 5.065c-.283.159-.593.243-.918.243zm4.896-7.269c-3.38 0-4.119-1.558-4.119-2.876 0-.142.114-.253.256-.253h1.141c.12 0 .218.083.244.194.198.813.58 1.258 2.478 1.258 1.528 0 2.118-.355 2.118-1.148 0-.471-.188-.813-2.291-1.046-2.228-.238-3.288-.917-3.288-2.399 0-1.375 1.152-2.494 3.766-2.494 2.724 0 3.565 1.236 3.705 2.745.02.144-.08.253-.214.253h-1.131c-.125 0-.231-.091-.254-.212-.204-1.045-.644-1.395-2.106-1.395-1.37 0-1.924.321-1.924 1.046 0 .548.236.783 2.223 1.005 2.272.257 3.355.789 3.355 2.443 0 1.498-1.227 2.617-4.022 2.617z" />
      </svg>
    ),
    httpx: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="18" rx="2" />
        <path d="M2 9h20M9 9v12" />
      </svg>
    ),
    importlib: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v6m0 8v6M2 12h6m8 0h6" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  };
  return icons[icon] || <div className="h-5 w-5 rounded bg-text-muted/30" />;
}

function About() {
  return (
    <div className="mx-auto w-full max-w-[900px] px-3 py-6 sm:px-4 sm:py-10">
      {/* Hero */}
      <div className="relative mb-12 overflow-hidden rounded-2xl border border-border bg-surface p-6 sm:p-10">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-foreground/5 blur-3xl" />
        <div className="absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-foreground/3 blur-2xl" />

        <div className="relative">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-foreground">
              <span className="text-lg font-bold text-background tracking-tighter">A·B</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Agent Black</h1>
              <p className="text-sm text-text-secondary">Multi-Agent Research Platform</p>
            </div>
          </div>

          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-text-secondary sm:text-base">
            Agent Black is a multi-agent research platform with specialized CV, NLP, and ML agents,
            coordinated by a host orchestrator through the A2A protocol and MCP tooling. The system is
            designed to support structured, end-to-end research workflows through a focused, professional interface.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href={PROJECT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:opacity-90 transition-opacity"
            >
              <Github className="h-4 w-4" />
              View on GitHub
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-surface-hover transition-colors"
            >
              Open Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Architecture at a glance */}
      <div className="mb-12 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Agents", value: "3", sub: "Research · Solution · Experiment" },
          { label: "MCP Tools", value: "39", sub: "13 tools per agent" },
          { label: "Protocol", value: "A2A", sub: "JSON-RPC 2.0" },
          { label: "LLM", value: "OpenAI", sub: "mimo-v2.5 via custom endpoint" },
        ].map((s) => (
          <div key={s.label} className="rounded-xl border border-border bg-surface p-4">
            <span className="text-[10px] uppercase tracking-wider text-text-muted">{s.label}</span>
            <div className="mt-1 text-xl font-bold tracking-tight">{s.value}</div>
            <p className="mt-0.5 text-[11px] text-text-muted">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Team */}
      <section className="mb-12">
        <h2 className="mb-1 text-lg font-semibold tracking-tight">Team</h2>
        <p className="mb-5 text-sm text-text-secondary">The team behind Agent Black.</p>

        <div className="grid gap-3 sm:grid-cols-3">
          {team.map((m, i) => (
            <a
              key={`${m.github}-${i}`}
              href={m.github}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative rounded-xl border border-border bg-surface p-5 transition-all hover:border-foreground/20 hover:shadow-md"
            >
              <div className="mb-3 flex items-center gap-3">
                <img
                  src={`https://avatars.githubusercontent.com/${m.github.replace("https://github.com/", "")}`}
                  alt={m.name}
                  className="h-10 w-10 rounded-full border border-border bg-surface object-cover"
                  loading="lazy"
                />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold group-hover:underline">{m.name}</div>
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
      <section className="mb-12">
        <h2 className="mb-1 text-lg font-semibold tracking-tight">Tech Stack</h2>
        <p className="mb-5 text-sm text-text-secondary">Technologies and libraries powering the platform.</p>

        <div className="space-y-4">
          {stack.map((group) => (
            <div key={group.category} className="rounded-xl border border-border bg-surface">
              <div className="border-b border-border-light px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
                {group.category}
              </div>
              <div className="grid grid-cols-1 divide-y divide-border-light sm:grid-cols-2 sm:divide-x sm:divide-y-0">
                {group.items.map((item) => (
                  <div key={item.name} className="flex items-center gap-3 px-4 py-3">
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

      {/* Footer */}
      <div className="border-t border-border pt-6 text-center text-xs text-text-muted">
        <p>
          Agent Black · Built with FastAPI, React, and Tailwind CSS
        </p>
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
