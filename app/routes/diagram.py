import sys
import os
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

SUBGRAPH_COLORS = {
    "user": "#FFF3E0",
    "agents": "#E8EAF6",
    "tools": "#E8F5E9",
    "llm": "#FCE4EC",
}

AGENT_TOOL_MAP = {
    "research": [
        ("paper_search", "Search Papers\n(arXiv, CrossRef, Semantic Scholar)"),
        ("cv_datasets", "CV Datasets\n(Papers With Code)"),
        ("cv_models", "CV Models\n(State-of-the-art)"),
    ],
    "solution": [
        ("nlp_datasets", "NLP Datasets\n(HuggingFace)"),
        ("rag_design", "RAG Design\n(Vector DB + LLM)"),
        ("llm_benchmark", "LLM Benchmark\n(MMLU, HumanEval)"),
    ],
    "experiment": [
        ("experiment_planner", "Experiment Planner\n(Reproducible setup)"),
        ("eval_metrics", "Eval Metrics\n(ML benchmarks)"),
        ("hyperparams", "Hyperparameters\n(Optuna tuning)"),
    ],
}

AGENT_LABELS = {
    "research": ("<b>Research Agent</b>\\n(CV) :8001", "research"),
    "solution": ("<b>Solution Agent</b>\\n(NLP) :8002", "solution"),
    "experiment": ("<b>Experiment Agent</b>\\n(ML) :8003", "experiment"),
}

REPORT_SECTION_LABELS = {
    "literature_review": "Literature Review",
    "datasets": "Datasets",
    "models": "Models",
    "evaluation_plan": "Evaluation Plan",
    "prototype_guidance": "Prototype Guidance",
}


def _escape_mmd(s: str) -> str:
    """Escape special characters for mermaid node labels."""
    return s.replace('"', "'").replace("\n", "\\n")


def generate_agent_flow_diagram(query: str = "", report: dict = None) -> str:
    lines = ["graph TD"]
    lines.append(f'    User["<b>User Query</b>"]:::userNode')
    lines.append(f'    User -->|"POST /research"| Host["<b>Host Agent</b>\\n:8000"]:::hostNode')

    lines.append(f'    Host -->|"decompose task"| Research["<b>Research Agent</b>\\n(CV) :8001"]:::agentNode')
    lines.append(f'    Host -->|"decompose task"| Solution["<b>Solution Agent</b>\\n(NLP) :8002"]:::agentNode')
    lines.append(f'    Host -->|"decompose task"| Experiment["<b>Experiment Agent</b>\\n(ML) :8003"]:::agentNode')

    lines.append(f'    Research --> T1["paper_search"]:::toolNode')
    lines.append(f'    Research --> T2["cv_datasets"]:::toolNode')
    lines.append(f'    Research --> T3["cv_models"]:::toolNode')

    lines.append(f'    Solution --> T4["nlp_datasets"]:::toolNode')
    lines.append(f'    Solution --> T5["rag_design"]:::toolNode')
    lines.append(f'    Solution --> T6["llm_benchmark"]:::toolNode')

    lines.append(f'    Experiment --> T7["experiment_planner"]:::toolNode')
    lines.append(f'    Experiment --> T8["eval_metrics"]:::toolNode')
    lines.append(f'    Experiment --> T9["hyperparams"]:::toolNode')

    lines.append(f'    T1 & T2 & T3 --> Research')
    lines.append(f'    T4 & T5 & T6 --> Solution')
    lines.append(f'    T7 & T8 & T9 --> Experiment')

    lines.append(f'    Research -->|"results"| Host')
    lines.append(f'    Solution -->|"results"| Host')
    lines.append(f'    Experiment -->|"results"| Host')

    lines.append(f'    Host -->|"synthesize"| Report["<b>Aggregated Report</b>\\nliterature_review\\ndatasets\\nmodels\\nevaluation_plan"]:::reportNode')

    lines.append(f'    subgraph LLM_Backend["<b>LLM Provider</b>"]')
    lines.append(f'        LLM["Gemini / OpenAI / Anthropic"]:::llmNode')
    lines.append(f'    end')
    lines.append(f'    Host -.->|"call_llm()"| LLM')
    lines.append(f'    Research -.->|"call_llm()"| LLM')
    lines.append(f'    Solution -.->|"call_llm()"| LLM')
    lines.append(f'    Experiment -.->|"call_llm()"| LLM')

    lines.append(f'    classDef userNode fill:{SUBGRAPH_COLORS["user"]},stroke:{AGENT_COLORS["user"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef hostNode fill:{SUBGRAPH_COLORS["agents"]},stroke:{AGENT_COLORS["host"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef agentNode fill:{SUBGRAPH_COLORS["agents"]},stroke:{AGENT_COLORS["research"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef toolNode fill:{SUBGRAPH_COLORS["tools"]},stroke:#2ECC71,stroke-width:2px,color:#333')
    lines.append(f'    classDef reportNode fill:{SUBGRAPH_COLORS["llm"]},stroke:#E74C3C,stroke-width:3px,color:#333')
    lines.append(f'    classDef llmNode fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#333')

    if query:
        lines.insert(1, f'    subgraph Query["<b>Query:</b> {_escape_mmd(query[:60])}"]')
        lines.insert(2, f'    end')

    return "\n".join(lines)


def _extract_items(report: dict, key: str, label_key: str = "title", max_items: int = 3) -> list[str]:
    """Extract a list of item previews from a report section."""
    val = report.get(key)
    if not val:
        return []
    if isinstance(val, str):
        items = [line.strip() for line in val.split("\n") if line.strip()][:max_items]
        if not items:
            items = [val[:60]]
        return items
    if isinstance(val, list):
        previews = []
        for item in val[:max_items]:
            if isinstance(item, dict):
                t = item.get(label_key, "") or item.get("name", "") or str(item.get("id", ""))
                previews.append(str(t)[:60])
            else:
                previews.append(str(item)[:60])
        return previews
    if isinstance(val, dict):
        return [f"{k}: {str(v)[:40]}" for k, v in list(val.items())[:max_items]]
    return [str(val)[:60]]


def generate_dynamic_diagram(query: str, report: dict, agents_used: list[str] = None, events: list[dict] = None) -> str:
    """Generate a mermaid diagram dynamically based on the actual report data for a specific project."""
    if not agents_used:
        agents_used = list(AGENT_TOOL_MAP.keys())

    lines = ["graph TD"]
    import json

    # ── Top: Query ──
    safe_query = _escape_mmd(query[:100])
    lines.append(f'    User["<b>Research Query</b>\\n{safe_query}"]:::userNode')

    # ── Host ──
    lines.append(f'    User -->|"submit"| Host["<b>Host Orchestrator</b>\\n:8000"]:::hostNode')

    # ── Specialized Agents ──
    lines.append(f'    subgraph agents_box["<b>Active Agents</b>"]')

    tool_idx = 0
    for agent in agents_used:
        if agent not in AGENT_LABELS:
            continue
        label, color_key = AGENT_LABELS[agent]
        node_id = f'Agent_{agent}'
        lines.append(f'    Host -->|"route"| {node_id}["{label}"]:::{color_key}Node')

        tools = AGENT_TOOL_MAP.get(agent, [])
        for tool_id, tool_label in tools:
            tool_node = f'T{tool_idx}'
            tool_idx += 1
            safe_label = _escape_mmd(tool_label)
            lines.append(f'    {node_id} --> {tool_node}["{safe_label}"]:::toolNode')
            lines.append(f'    {tool_node} --> {node_id}')

    lines.append(f'    end')

    # ── Agent Results (findings from each agent) ──
    agent_findings = {
        "research": _extract_items(report, "literature_review", max_items=2),
        "solution": _extract_items(report, "models", max_items=2),
        "experiment": _extract_items(report, "evaluation_plan", max_items=2),
    }
    finding_idx = 0
    finding_nodes = []
    for agent in agents_used:
        findings = agent_findings.get(agent, [])
        if findings:
            for f_text in findings:
                fid = f'F{finding_idx}'
                finding_idx += 1
                safe_f = _escape_mmd(f_text[:55])
                lines.append(f'    Agent_{agent} -->|"discovers"| {fid}["{safe_f}"]:::findingNode')
                finding_nodes.append(fid)

    # ── Report Sections ──
    has_report = isinstance(report, dict) and any(report.get(k) for k in REPORT_SECTION_LABELS)
    if has_report:
        lines.append(f'    subgraph report_box["<b>Research Findings</b>"]')
        section_nodes = []
        for key, label in REPORT_SECTION_LABELS.items():
            raw_val = report.get(key)
            if not raw_val:
                continue
            nid = f'S_{key}'
            if isinstance(raw_val, str):
                preview = raw_val[:80].replace("\n", " ")
            elif isinstance(raw_val, (list, dict)):
                preview = json.dumps(raw_val, ensure_ascii=False)[:80]
            else:
                preview = str(raw_val)[:80]
            safe_preview = _escape_mmd(preview)
            lines.append(f'    {nid}["<b>{label}</b>\\n{safe_preview}"]:::reportNode')
            section_nodes.append(nid)
            for fid in finding_nodes:
                lines.append(f'    {fid} -.-> {nid}')
        lines.append(f'    end')

        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    Agent_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"synthesize"| report_box')

    else:
        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    Agent_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"generate"| Report["<b>Aggregated Report</b>"]:::reportNode')

    # ── Datasets subsection ──
    datasets = _extract_items(report, "datasets", label_key="name", max_items=4)
    if datasets:
        lines.append(f'    subgraph datasets_box["<b>Datasets &amp; Benchmarks</b>"]')
        ds_nodes = []
        for i, ds in enumerate(datasets):
            dn = f'DS{i}'
            safe_ds = _escape_mmd(ds[:60])
            lines.append(f'    {dn}["📊 {safe_ds}"]:::datasetNode')
            ds_nodes.append(dn)
        lines.append(f'    end')
        if has_report:
            for ds_n in ds_nodes:
                lines.append(f'    {"S_datasets" if "S_datasets" in [f"S_{k}" for k in REPORT_SECTION_LABELS] else "report_box"} -.-> {ds_n}')

    # ── LLM Backend ──
    lines.append(f'    subgraph LLM_Backend["<b>LLM Backend</b>"]')
    lines.append(f'        LLM["Gemini 2.5 / OpenAI / Anthropic"]:::llmNode')
    lines.append(f'    end')
    for agent in agents_used:
        if agent in AGENT_LABELS:
            lines.append(f'    Agent_{agent} -.->|"call_llm()"| LLM')
    lines.append(f'    Host -.->|"call_llm()"| LLM')

    # ── Execution Timeline ──
    if events and len(events) > 1:
        lines.append(f'    subgraph timeline_box["<b>Execution Timeline</b>"]')
        prev_ev = None
        for i, ev in enumerate(events[:10]):
            step = ev.get("step", f"step_{i}")
            status = ev.get("status", "")
            safe_step = _escape_mmd(step[:50])
            nid = f'Ev{i}'
            status_icon = "✅" if status == "complete" else "⏳" if status == "running" else "❌" if status == "error" else "▸"
            lines.append(f'    {nid}["{status_icon} {safe_step}"]:::timelineNode')
            if prev_ev:
                lines.append(f'    {prev_ev} --> {nid}')
            prev_ev = nid
        lines.append(f'    end')

    # ── Style definitions ──
    lines.append(f'    classDef userNode fill:{SUBGRAPH_COLORS["user"]},stroke:{AGENT_COLORS["user"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef hostNode fill:{SUBGRAPH_COLORS["agents"]},stroke:{AGENT_COLORS["host"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef researchNode fill:#E8EAF6,stroke:{AGENT_COLORS["research"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef solutionNode fill:#E8EAF6,stroke:{AGENT_COLORS["solution"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef experimentNode fill:#E8EAF6,stroke:{AGENT_COLORS["experiment"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef toolNode fill:{SUBGRAPH_COLORS["tools"]},stroke:#2ECC71,stroke-width:2px,color:#333')
    lines.append(f'    classDef reportNode fill:{SUBGRAPH_COLORS["llm"]},stroke:#E74C3C,stroke-width:2px,color:#333')
    lines.append(f'    classDef findingNode fill:#E3F2FD,stroke:#1565C0,stroke-width:1.5px,color:#333')
    lines.append(f'    classDef datasetNode fill:#E8F5E9,stroke:#2E7D32,stroke-width:1.5px,color:#333')
    lines.append(f'    classDef llmNode fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#333')
    lines.append(f'    classDef timelineNode fill:#FFF8E1,stroke:#FF9800,stroke-width:1px,color:#333')

    return "\n".join(lines)


def generate_tech_stack_diagram(preferences: dict = None) -> str:
    lines = ["graph LR"]
    lines.append(f'    UI[\"<b>React Frontend</b>\\nMonochrome UI\"]:::frontendNode')
    lines.append(f'    UI -->|"POST /api/query"| API[\"<b>FastAPI Control</b>\\n:8000/api\"]:::apiNode')

    lines.append(f'    API -->|"orchestrate"| Host[\"<b>Host Agent</b>\\n:8000\"]:::hostNode')
    lines.append(f'    Host --> Research[\"<b>Research Agent</b>\\n:8001\"]:::agentNode')
    lines.append(f'    Host --> Solution[\"<b>Solution Agent</b>\\n:8002\"]:::agentNode')
    lines.append(f'    Host --> Experiment[\"<b>Experiment Agent</b>\\n:8003\"]:::agentNode')

    lines.append(f'    Research --> Paper[\"arxiv API\\npaper_search\"]:::toolNode')
    lines.append(f'    Solution --> Rag[\"RAG Design\\nrag_design\"]:::toolNode')
    lines.append(f'    Experiment --> Metrics[\"Metric Advisor\\neval_metrics\"]:::toolNode')

    lines.append(f'    subgraph LLM[\"LLM Provider\"]')
    lines.append(f'        Gemini[\"Gemini\"]')
    lines.append(f'        OpenAI[\"OpenAI\"]')
    lines.append(f'        Anthropic[\"Anthropic\"]')
    lines.append(f'    end')

    lines.append(f'    Research -.-> LLM')
    lines.append(f'    Solution -.-> LLM')
    lines.append(f'    Experiment -.-> LLM')

    lines.append(f'    subgraph Deploy[\"Deployment\"]')
    lines.append(f'        Docker[\"Docker Compose\"]')
    lines.append(f'    end')

    lines.append(f'    Host -.-> Docker')
    lines.append(f'    Research -.-> Docker')
    lines.append(f'    Solution -.-> Docker')
    lines.append(f'    Experiment -.-> Docker')

    lines.append(f'    classDef frontendNode fill:#1a1a2e,stroke:#e0e0e0,stroke-width:2px,color:#e0e0e0')
    lines.append(f'    classDef apiNode fill:#16213e,stroke:#e0e0e0,stroke-width:2px,color:#e0e0e0')
    lines.append(f'    classDef hostNode fill:#0f3460,stroke:#e94560,stroke-width:3px,color:#e0e0e0')
    lines.append(f'    classDef agentNode fill:#0f3460,stroke:#e94560,stroke-width:2px,color:#e0e0e0')
    lines.append(f'    classDef toolNode fill:#1a1a2e,stroke:#533483,stroke-width:2px,color:#e0e0e0')

    return "\n".join(lines)


@router.post("/diagram/agent-flow", response_model=DiagramResponse)
def agent_flow_diagram(req: DiagramRequest):
    diagram = generate_agent_flow_diagram(req.query or "")
    return DiagramResponse(
        diagram=diagram,
        description="Agent-to-Agent (A2A) flow diagram showing how the Host Agent decomposes tasks and routes them to specialized agents."
    )


@router.post("/diagram/tech-stack", response_model=DiagramResponse)
def tech_stack_diagram(req: DiagramRequest):
    diagram = generate_tech_stack_diagram()
    return DiagramResponse(
        diagram=diagram,
        description="Technology stack diagram showing the full architecture from React frontend to LLM providers."
    )


@router.post("/diagram/from-report", response_model=DiagramResponse)
def diagram_from_report(req: DiagramFromReportRequest):
    """Generate a dynamic diagram based on the actual report data for a specific project."""
    diagram = generate_dynamic_diagram(
        query=req.query,
        report=req.report,
        agents_used=req.agents_used,
        events=req.events,
    )
    return DiagramResponse(
        diagram=diagram,
        description=f"Dynamic diagram for query: {req.query[:80]}. Shows agents used: {', '.join(req.agents_used) if req.agents_used else 'all'}."
    )
