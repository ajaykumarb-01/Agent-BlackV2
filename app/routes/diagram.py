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

    lines.append(f'    T1 --> Research')
    lines.append(f'    T2 --> Research')
    lines.append(f'    T3 --> Research')
    lines.append(f'    T4 --> Solution')
    lines.append(f'    T5 --> Solution')
    lines.append(f'    T6 --> Solution')
    lines.append(f'    T7 --> Experiment')
    lines.append(f'    T8 --> Experiment')
    lines.append(f'    T9 --> Experiment')

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


def generate_dynamic_diagram(query: str, report: dict, agents_used: list[str] = None, events: list[dict] = None) -> str:
    """Generate a mermaid diagram dynamically based on the actual report data for a specific project."""
    if not agents_used:
        agents_used = list(AGENT_TOOL_MAP.keys())

    lines = ["graph TD"]

    # Query node
    safe_query = _escape_mmd(query[:80])
    lines.append(f'    User["<b>User Query</b>\\n{safe_query}"]:::userNode')

    # Host node
    lines.append(f'    User -->|"submit"| Host["<b>Host Orchestrator</b>\\n:8000"]:::hostNode')

    # Subgraph for active agents
    lines.append(f'    subgraph agents_box["<b>Specialized Agents</b>"]')

    tool_idx = 0
    for agent in agents_used:
        if agent not in AGENT_LABELS:
            continue
        label, color_key = AGENT_LABELS[agent]
        node_id = f'Agent_{agent}'
        lines.append(f'    Host -->|"route"| {node_id}["{label}"]:::{color_key}Node')

        # Show only tools relevant to this agent from the report
        tools = AGENT_TOOL_MAP.get(agent, [])
        for tool_id, tool_label in tools:
            tool_node = f'T{tool_idx}'
            tool_idx += 1
            safe_label = _escape_mmd(tool_label)
            lines.append(f'    {node_id} --> {tool_node}["{safe_label}"]:::toolNode')
            lines.append(f'    {tool_node} --> {node_id}')

    lines.append(f'    end')

    # Report sections — show only sections that have data
    report_node_id = None
    has_report = isinstance(report, dict) and any(report.get(k) for k in REPORT_SECTION_LABELS)
    if has_report:
        lines.append(f'    subgraph report_box["<b>Report Sections</b>"]')
        section_nodes = []
        for key, label in REPORT_SECTION_LABELS.items():
            if report.get(key):
                nid = f'S_{key}'
                # Truncate content preview
                raw_val = report[key]
                if isinstance(raw_val, str):
                    preview = raw_val[:60].replace("\n", " ")
                elif isinstance(raw_val, (list, dict)):
                    import json
                    preview = json.dumps(raw_val, ensure_ascii=False)[:60]
                else:
                    preview = str(raw_val)[:60]
                safe_preview = _escape_mmd(preview)
                lines.append(f'    {nid}["<b>{label}</b>\\n{safe_preview}"]:::reportNode')
                section_nodes.append(nid)
        lines.append(f'    end')

        # Agents return results to host, host synthesizes report
        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    Agent_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"synthesize"| report_box')

    else:
        # No report data — just show agents returning to host
        for agent in agents_used:
            if agent in AGENT_LABELS:
                lines.append(f'    Agent_{agent} -->|"results"| Host')
        lines.append(f'    Host -->|"generate"| Report["<b>Report</b>"]:::reportNode')

    # LLM backend (dashed)
    lines.append(f'    subgraph LLM_Backend["<b>LLM Provider</b>"]')
    lines.append(f'        LLM["LLM API"]:::llmNode')
    lines.append(f'    end')
    for agent in agents_used:
        if agent in AGENT_LABELS:
            lines.append(f'    Agent_{agent} -.->|"call_llm()"| LLM')
    lines.append(f'    Host -.->|"call_llm()"| LLM')

    # Progress events as timeline (if provided)
    if events and len(events) > 1:
        lines.append(f'    subgraph timeline_box["<b>Execution Timeline</b>"]')
        prev_ev = None
        for i, ev in enumerate(events[:8]):  # limit to 8 steps
            step = ev.get("step", f"step_{i}")
            status = ev.get("status", "")
            safe_step = _escape_mmd(step[:40])
            nid = f'Ev{i}'
            status_icon = "✅" if status == "complete" else "⏳" if status == "running" else "❌" if status == "error" else "•"
            lines.append(f'    {nid}["{status_icon} {safe_step}"]:::timelineNode')
            if prev_ev:
                lines.append(f'    {prev_ev} --> {nid}')
            prev_ev = nid
        lines.append(f'    end')

    # Style definitions
    lines.append(f'    classDef userNode fill:{SUBGRAPH_COLORS["user"]},stroke:{AGENT_COLORS["user"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef hostNode fill:{SUBGRAPH_COLORS["agents"]},stroke:{AGENT_COLORS["host"]},stroke-width:3px,color:#333')
    lines.append(f'    classDef researchNode fill:#E8EAF6,stroke:{AGENT_COLORS["research"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef solutionNode fill:#E8EAF6,stroke:{AGENT_COLORS["solution"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef experimentNode fill:#E8EAF6,stroke:{AGENT_COLORS["experiment"]},stroke-width:2px,color:#333')
    lines.append(f'    classDef toolNode fill:{SUBGRAPH_COLORS["tools"]},stroke:#2ECC71,stroke-width:2px,color:#333')
    lines.append(f'    classDef reportNode fill:{SUBGRAPH_COLORS["llm"]},stroke:#E74C3C,stroke-width:2px,color:#333')
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
