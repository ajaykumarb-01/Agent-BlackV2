import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter
from app.models import DiagramRequest, DiagramResponse, DiagramFromReportRequest
from typing import Any

router = APIRouter(tags=["diagram"])

AGENT_COLORS = {
    "host": "#4A90D9",
    "research": "#7B68EE",
    "solution": "#2ECC71",
    "experiment": "#E74C3C",
    "user": "#F39C12",
}

AGENT_LABELS = {
    "research": "<b>Research Agent</b>\\n(CV) :8001",
    "solution": "<b>Solution Agent</b>\\n(NLP) :8002",
    "experiment": "<b>Experiment Agent</b>\\n(ML) :8003",
}

REPORT_SECTION_LABELS = {
    "literature_review": "Literature Review",
    "datasets": "Datasets",
    "models": "Models",
    "evaluation_plan": "Evaluation Plan",
    "prototype_guidance": "Prototype Guidance",
}

# Fallback tools when no event data is available
_FALLBACK_TOOLS = {
    "research": ["paper_search", "cv_datasets", "cv_models"],
    "solution": ["nlp_datasets", "rag_design", "llm_benchmark"],
    "experiment": ["experiment_planner", "eval_metrics", "hyperparams"],
}

TOOL_DISPLAY_NAMES: dict[str, str] = {
    "paper_search": "Paper Search",
    "cv_datasets": "CV Datasets",
    "cv_models": "CV Models",
    "cv_papers": "CV Papers",
    "benchmark_search": "Benchmark Search",
    "citation_generator": "Citations",
    "experiment_planner": "Experiment Planner",
    "explainability": "Explainability",
    "feature_engineering": "Feature Eng.",
    "gap_analysis": "Gap Analysis",
    "hyperparams": "Hyperparameters",
    "metrics": "Metrics",
    "models_tool": "Models",
    "prototype_guidance": "Prototype Guide",
    "solution_recommendation": "Solution Rec.",
    "summarizer": "Summarizer",
    "time_series": "Time Series",
    "architecture_comparison": "Arch. Compare",
    "eval_advisor": "Eval Advisor",
    "synthetic_data": "Synthetic Data",
    "nlp_datasets": "NLP Datasets",
    "rag_design": "RAG Design",
    "llm_benchmark": "LLM Benchmark",
    "eval_metrics": "Eval Metrics",
    "information_extraction": "Info Extraction",
    "prompt_optimizer": "Prompt Optimizer",
    "solution_recommendation": "Solution Rec.",
}


def _esc(s: str) -> str:
    """Escape for mermaid node labels."""
    return (
        s.replace('"', "'")
        .replace("\n", " ")
        .replace("#", " ")
        .replace("<", "lt")
        .replace(">", "gt")
        .replace("&", "and")
        .replace("{", "(")
        .replace("}", ")")
        .strip()
    )


def _tool_label(name: str) -> str:
    return TOOL_DISPLAY_NAMES.get(name, name.replace("_", " ").title())


def _extract_tools_from_events(events: list[dict]) -> dict[str, list[str]]:
    """Parse routing events to find actual agent-to-tool mapping."""
    result: dict[str, list[str]] = {}
    for ev in events:
        if ev.get("step") == "routing" and ev.get("status") == "complete":
            try:
                parsed = json.loads(ev.get("detail", "{}"))
                agents_data = parsed.get("agents", [])
                if isinstance(agents_data, list):
                    for a in agents_data:
                        if isinstance(a, dict):
                            name = a.get("name", "")
                            tools = a.get("tools", [])
                            if name and tools:
                                result[name] = tools
                        elif isinstance(a, str):
                            result[a] = []
            except (json.JSONDecodeError, TypeError):
                pass
    return result


def _extract_findings(report: dict, key: str, max_items: int = 4) -> list[str]:
    """Extract meaningful findings from a report section."""
    val = report.get(key)
    if not val:
        return []
    if isinstance(val, str):
        lines = [line.strip() for line in val.split("\n") if line.strip() and len(line.strip()) > 5]
        return lines[:max_items] if lines else [val[:100]]
    if isinstance(val, list):
        previews = []
        for item in val[:max_items]:
            if isinstance(item, dict):
                t = item.get("title") or item.get("name") or item.get("id") or ""
                desc = item.get("description") or item.get("purpose") or item.get("key_finding") or ""
                if t and desc:
                    previews.append(f"{str(t)[:40]}: {str(desc)[:50]}")
                elif t:
                    previews.append(str(t)[:80])
                elif desc:
                    previews.append(str(desc)[:80])
                else:
                    previews.append(json.dumps(item, ensure_ascii=False)[:80])
            else:
                previews.append(str(item)[:80])
        return previews
    if isinstance(val, dict):
        text = val.get("text") or val.get("summary") or ""
        if text and isinstance(text, str):
            return [line.strip() for line in text.split("\n") if line.strip()][:max_items]
        items = []
        for k, v in list(val.items())[:max_items]:
            if k == "text":
                continue
            items.append(f"{k}: {str(v)[:60]}")
        return items
    return [str(val)[:80]]


def _style_defs() -> list[str]:
    return [
        'classDef userNode fill:#FFF3E0,stroke:#F39C12,stroke-width:3px,color:#333',
        'classDef hostNode fill:#E8EAF6,stroke:#4A90D9,stroke-width:3px,color:#333',
        'classDef agentNode fill:#F3E5F5,stroke:#7B68EE,stroke-width:2px,color:#333',
        'classDef toolNode fill:#E8F5E9,stroke:#2ECC71,stroke-width:2px,color:#333',
        'classDef findingNode fill:#E3F2FD,stroke:#1565C0,stroke-width:1.5px,color:#333',
        'classDef reportNode fill:#FCE4EC,stroke:#E74C3C,stroke-width:2px,color:#333',
        'classDef techNode fill:#E0F2F1,stroke:#00695C,stroke-width:1.5px,color:#333',
        'classDef llmNode fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#333',
        'classDef timelineNode fill:#FFF8E1,stroke:#FF9800,stroke-width:1px,color:#333',
        'classDef datasetNode fill:#E8F5E9,stroke:#2E7D32,stroke-width:1.5px,color:#333',
    ]


def generate_dynamic_diagram(
    query: str,
    report: dict,
    agents_used: list[str] | None = None,
    events: list[dict[str, Any]] | None = None,
    raw: dict[str, Any] | None = None,
) -> str:
    """Generate a mermaid diagram dynamically based on actual project execution data."""
    if not agents_used:
        agents_used = list(_FALLBACK_TOOLS.keys())
    if not events:
        events = []

    # Use raw events if available (full TaskResult from backend)
    all_events = list(events)
    if raw and isinstance(raw.get("events"), list):
        all_events = raw["events"]

    # ── Extract actual tools per agent from events ──
    tool_map = _extract_tools_from_events(all_events)
    for agent in agents_used:
        if agent not in tool_map:
            tool_map[agent] = _FALLBACK_TOOLS.get(agent, [])

    lines = ["graph TD"]

    # ── 1. User Query ──
    safe_query = _esc(query[:80])
    lines.append(f'    User["<b>Research Query</b>\\n{safe_query}"]:::userNode')

    # ── 2. Host Orchestrator ──
    lines.append(f'    User -->|"submit query"| Host["<b>Host Orchestrator</b>\\nrelevance gate → routing → dispatch → aggregation"]:::hostNode')

    # ── 3. Selected Agents with their actual tools ──
    agent_names_display = []
    for agent in agents_used:
        if agent not in AGENT_LABELS:
            continue
        agent_names_display.append(agent)
        node_id = f"A_{agent}"
        label = AGENT_LABELS[agent]
        lines.append(f'    Host -->|"route"| {node_id}["{label}"]:::agentNode')

        tools = tool_map.get(agent, [])
        for i, tool_name in enumerate(tools):
            tid = f"T_{agent}_{i}"
            tlabel = _esc(_tool_label(tool_name))
            lines.append(f'    {node_id} --> {tid}["{tlabel}"]:::toolNode')

    # ── 4. Agent Findings from report sections ──
    finding_map = {
        "research": [("literature_review", "Papers"), ("datasets", "Datasets")],
        "solution": [("models", "Models"), ("prototype_guidance", "Guidance")],
        "experiment": [("evaluation_plan", "Eval Plan"), ("models", "Models")],
    }

    finding_nodes: list[str] = []
    fidx = 0
    for agent in agents_used:
        sections = finding_map.get(agent, [])
        for section_key, prefix in sections:
            findings = _extract_findings(report, section_key, max_items=2)
            for text in findings:
                fid = f"F{fidx}"
                fidx += 1
                safe_text = _esc(f"{prefix}: {text[:80]}")
                lines.append(f'    A_{agent} -->|"discovers"| {fid}["{safe_text}"]:::findingNode')
                finding_nodes.append(fid)

    # ── 5. Report Sections ──
    report_keys_present = [k for k in REPORT_SECTION_LABELS if report.get(k)]
    if report_keys_present:
        lines.append(f'    subgraph report_box["<b>Research Report</b>"]')
        section_node_ids = []
        for key in report_keys_present:
            label = REPORT_SECTION_LABELS[key]
            nid = f"S_{key}"
            section_node_ids.append(nid)
            lines.append(f'    {nid}["<b>{label}</b>"]:::reportNode')
        lines.append(f'    end')

        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    A_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"synthesize"| report_box')

        # Connect findings to sections
        for fid in finding_nodes:
            for nid in section_node_ids:
                lines.append(f'    {fid} -.-> {nid}')
    else:
        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    A_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"generate"| Report["<b>Report</b>"]:::reportNode')

    # ── 6. Tech Stack (from report) ──
    tech_stack = report.get("tech_stack", [])
    if isinstance(tech_stack, list) and tech_stack:
        lines.append(f'    subgraph tech_box["<b>Recommended Tech Stack</b>"]')
        for i, tech in enumerate(tech_stack[:8]):
            tid = f"Tech{i}"
            safe_tech = _esc(str(tech)[:40])
            lines.append(f'    {tid}["{safe_tech}"]:::techNode')
        lines.append(f'    end')
        if report_keys_present:
            lines.append(f'    report_box -.-> tech_box')

    # ── 7. Datasets (from report) ──
    datasets = _extract_findings(report, "datasets", max_items=4)
    if datasets:
        lines.append(f'    subgraph ds_box["<b>Datasets</b>"]')
        for i, ds in enumerate(datasets):
            dn = f"DS{i}"
            safe_ds = _esc(ds[:70])
            lines.append(f'    {dn}["{safe_ds}"]:::datasetNode')
        lines.append(f'    end')

    # ── 8. LLM Backend ──
    lines.append(f'    subgraph LLM["<b>LLM Backend</b>"]')
    lines.append(f'        LLMNode["Gemini / OpenAI / Anthropic"]:::llmNode')
    lines.append(f'    end')
    lines.append(f'    Host -.->|"call_llm"| LLMNode')
    for agent in agents_used:
        if agent in AGENT_LABELS:
            lines.append(f'    A_{agent} -.->|"call_llm"| LLMNode')

    # ── 9. Execution Timeline (from events) ──
    if all_events and len(all_events) > 1:
        complete_events = [e for e in all_events if e.get("status") == "complete" and e.get("step") not in ("submitted",)]
        if complete_events:
            lines.append(f'    subgraph timeline["<b>Execution Timeline</b>"]')
            prev_id = None
            for i, ev in enumerate(complete_events[:12]):
                step = ev.get("step", "")
                status_icon = "✅"
                if step in ("research", "solution", "experiment"):
                    step_label = f"{step.title()} Agent"
                elif step == "routing":
                    step_label = "Agent Routing"
                elif step == "aggregating":
                    step_label = "Aggregation"
                elif step == "validating_query":
                    step_label = "Query Validation"
                elif step == "discovering_agents":
                    step_label = "Agent Discovery"
                else:
                    step_label = step.replace("_", " ").title()
                nid = f"Ev{i}"
                safe_label = _esc(f"{status_icon} {step_label}")
                lines.append(f'    {nid}["{safe_label}"]:::timelineNode')
                if prev_id:
                    lines.append(f'    {prev_id} --> {nid}')
                prev_id = nid
            lines.append(f'    end')

    # ── Styles ──
    lines.extend(_style_defs())

    return "\n".join(lines)


def generate_agent_flow_diagram(
    query: str = "",
    report: dict | None = None,
    agents_used: list[str] | None = None,
    events: list[dict] | None = None,
) -> str:
    """Architecture flow diagram — uses report data if available, else shows system overview."""
    if report and agents_used:
        return generate_dynamic_diagram(
            query=query,
            report=report,
            agents_used=agents_used,
            events=events,
        )

    # Static fallback: system architecture overview
    lines = ["graph TD"]
    lines.append(f'    User["<b>User</b>"]:::userNode')
    lines.append(f'    User -->|"POST /api/query"| Host["<b>Control Panel</b>\\n:8000"]:::hostNode')
    lines.append(f'    Host -->|"A2A protocol"| Research["<b>Research Agent</b>\\n(CV) :8001"]:::agentNode')
    lines.append(f'    Host -->|"A2A protocol"| Solution["<b>Solution Agent</b>\\n(NLP) :8002"]:::agentNode')
    lines.append(f'    Host -->|"A2A protocol"| Experiment["<b>Experiment Agent</b>\\n(ML) :8003"]:::agentNode')

    lines.append(f'    Research --> R1["Paper Search"]:::toolNode')
    lines.append(f'    Research --> R2["CV Datasets"]:::toolNode')
    lines.append(f'    Research --> R3["Gap Analysis"]:::toolNode')
    lines.append(f'    Solution --> S1["NLP Datasets"]:::toolNode')
    lines.append(f'    Solution --> S2["RAG Design"]:::toolNode')
    lines.append(f'    Solution --> S3["LLM Benchmark"]:::toolNode')
    lines.append(f'    Experiment --> E1["Experiment Planner"]:::toolNode')
    lines.append(f'    Experiment --> E2["Eval Metrics"]:::toolNode')
    lines.append(f'    Experiment --> E3["Hyperparameters"]:::toolNode')

    lines.append(f'    R1 & R2 & R3 --> Research')
    lines.append(f'    S1 & S2 & S3 --> Solution')
    lines.append(f'    E1 & E2 & E3 --> Experiment')

    lines.append(f'    Research -->|"results"| Host')
    lines.append(f'    Solution -->|"results"| Host')
    lines.append(f'    Experiment -->|"results"| Host')
    lines.append(f'    Host -->|"synthesize"| Report["<b>Aggregated Report</b>"]:::reportNode')

    lines.append(f'    subgraph LLM["<b>LLM Provider</b>"]')
    lines.append(f'        LLMNode["Gemini / OpenAI / Anthropic"]:::llmNode')
    lines.append(f'    end')
    lines.append(f'    Host -.->|"call_llm"| LLMNode')
    lines.append(f'    Research -.->|"call_llm"| LLMNode')
    lines.append(f'    Solution -.->|"call_llm"| LLMNode')
    lines.append(f'    Experiment -.->|"call_llm"| LLMNode')

    lines.extend(_style_defs())

    if query:
        lines.insert(1, f'    subgraph Query["<b>Query:</b> {_esc(query[:60])}"]')
        lines.insert(2, f'    end')

    return "\n".join(lines)


def generate_tech_stack_diagram(
    report: dict | None = None,
    preferences: dict | None = None,
) -> str:
    """Tech stack diagram — uses actual tech stack from report if available."""
    tech_stack = []
    if report and isinstance(report.get("tech_stack"), list):
        tech_stack = report["tech_stack"]

    lines = ["graph LR"]
    lines.append(f'    UI["<b>React Frontend</b>\\nTanStack + Vite"]:::frontendNode')
    lines.append(f'    UI -->|"REST + SSE"| API["<b>FastAPI Control Panel</b>\\n:8000"]:::apiNode')

    lines.append(f'    API -->|"orchestrate"| Host["<b>Host Orchestrator</b>\\nrelevance → routing → dispatch → aggregate"]:::hostNode')
    lines.append(f'    Host -->|"A2A / JSON-RPC"| Research["<b>Research Agent</b>\\n(CV) :8001"]:::agentNode')
    lines.append(f'    Host -->|"A2A / JSON-RPC"| Solution["<b>Solution Agent</b>\\n(NLP) :8002"]:::agentNode')
    lines.append(f'    Host -->|"A2A / JSON-RPC"| Experiment["<b>Experiment Agent</b>\\n(ML) :8003"]:::agentNode')

    lines.append(f'    Research --> Paper["arXiv, CrossRef\\nSemantic Scholar"]:::toolNode')
    lines.append(f'    Solution --> Rag["RAG, Vector DB\\nLLM Benchmarking"]:::toolNode')
    lines.append(f'    Experiment --> Metrics["ML Benchmarks\\nOptuna, Hyperparams"]:::toolNode')

    lines.append(f'    subgraph LLM["<b>LLM Provider</b>"]')
    lines.append(f'        Gemini["Gemini"]')
    lines.append(f'        OpenAI["OpenAI"]')
    lines.append(f'        Anthropic["Anthropic"]')
    lines.append(f'    end')
    lines.append(f'    Research -.-> LLM')
    lines.append(f'    Solution -.-> LLM')
    lines.append(f'    Experiment -.-> LLM')

    # Show actual tech stack from report if available
    if tech_stack:
        lines.append(f'    subgraph RecommendedTech["<b>Recommended Tech</b>"]')
        for i, tech in enumerate(tech_stack[:10]):
            tid = f"Tech{i}"
            safe_t = _esc(str(tech)[:35])
            lines.append(f'    {tid}["{safe_t}"]:::techNode')
        lines.append(f'    end')

    lines.append(f'    subgraph Deploy["<b>Deployment</b>"]')
    lines.append(f'        Docker["Docker Compose"]')
    lines.append(f'        GHCR["GHCR Registry"]')
    lines.append(f'    end')
    lines.append(f'    Host -.-> Docker')

    lines.extend(_style_defs())
    lines.append(f'    classDef frontendNode fill:#1a1a2e,stroke:#e0e0e0,stroke-width:2px,color:#e0e0e0')
    lines.append(f'    classDef apiNode fill:#16213e,stroke:#e0e0e0,stroke-width:2px,color:#e0e0e0')

    return "\n".join(lines)


# ── API Routes ──────────────────────────────────────────────────────────────


@router.post("/diagram/agent-flow", response_model=DiagramResponse)
def agent_flow_diagram(req: DiagramRequest):
    diagram = generate_agent_flow_diagram(
        query=req.query or "",
        report=req.report,
        agents_used=req.agents_used,
        events=req.events,
    )
    return DiagramResponse(
        diagram=diagram,
        description="System architecture flow showing Host Agent orchestration across specialist agents.",
    )


@router.post("/diagram/tech-stack", response_model=DiagramResponse)
def tech_stack_diagram(req: DiagramRequest):
    diagram = generate_tech_stack_diagram(report=req.report)
    return DiagramResponse(
        diagram=diagram,
        description="Technology stack from React frontend through multi-agent orchestration to LLM providers.",
    )


@router.post("/diagram/from-report", response_model=DiagramResponse)
def diagram_from_report(req: DiagramFromReportRequest):
    """Generate a dynamic diagram based on actual execution data for a specific query."""
    diagram = generate_dynamic_diagram(
        query=req.query,
        report=req.report,
        agents_used=req.agents_used,
        events=req.events,
        raw=req.raw,
    )
    agents_str = ", ".join(req.agents_used) if req.agents_used else "all"
    return DiagramResponse(
        diagram=diagram,
        description=f"Project diagram for: {req.query[:80]}. Agents: {agents_str}.",
    )
