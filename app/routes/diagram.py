import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter
from app.models import DiagramRequest, DiagramResponse
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


def generate_agent_flow_diagram(query: str = "", report: dict = None) -> str:
    lines = ["graph TD"]
    lines.append(f'    User[\"<b>User Query</b>\"]:::userNode')
    lines.append(f'    User -->|"POST /research"| Host[\"<b>Host Agent</b>\\n:8000\"]:::hostNode')

    lines.append(f'    Host -->|"decompose task"| Research[\"<b>Research Agent</b>\\n(CV) :8001\"]:::agentNode')
    lines.append(f'    Host -->|"decompose task"| Solution[\"<b>Solution Agent</b>\\n(NLP) :8002\"]:::agentNode')
    lines.append(f'    Host -->|"decompose task"| Experiment[\"<b>Experiment Agent</b>\\n(ML) :8003\"]:::agentNode')

    lines.append(f'    Research --> T1[\"paper_search\"]:::toolNode')
    lines.append(f'    Research --> T2[\"cv_datasets\"]:::toolNode')
    lines.append(f'    Research --> T3[\"cv_models\"]:::toolNode')

    lines.append(f'    Solution --> T4[\"nlp_datasets\"]:::toolNode')
    lines.append(f'    Solution --> T5[\"rag_design\"]:::toolNode')
    lines.append(f'    Solution --> T6[\"llm_benchmark\"]:::toolNode')

    lines.append(f'    Experiment --> T7[\"experiment_planner\"]:::toolNode')
    lines.append(f'    Experiment --> T8[\"eval_metrics\"]:::toolNode')
    lines.append(f'    Experiment --> T9[\"hyperparams\"]:::toolNode')

    lines.append(f'    T1 & T2 & T3 --> Research')
    lines.append(f'    T4 & T5 & T6 --> Solution')
    lines.append(f'    T7 & T8 & T9 --> Experiment')

    lines.append(f'    Research -->|"results"| Host')
    lines.append(f'    Solution -->|"results"| Host')
    lines.append(f'    Experiment -->|"results"| Host')

    lines.append(f'    Host -->|"synthesize"| Report[\"<b>Aggregated Report</b>\\nliterature_review\\ndatasets\\nmodels\\nevaluation_plan\"]:::reportNode')

    lines.append(f'    subgraph LLM_Backend[\"<b>LLM Provider</b>\"]')
    lines.append(f'        LLM[\"Gemini / OpenAI / Anthropic\"]:::llmNode')
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
        lines.insert(1, f'    subgraph Query[\"<b>Query:</b> {query[:50]}\"]')
        lines.insert(2, f'    end')

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
