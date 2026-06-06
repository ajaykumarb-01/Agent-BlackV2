# Generic Multi-Agent Research Ecosystem — Implementation Plan

> **Assignment:** Multi-Agent Research Assistant Ecosystem using MCP and A2A  
> **Stack:** Python · FastAPI · LLM (Gemini / NVIDIA) · Docker  
> **Your Role:** Build one Specialized Agent + MCP Server + A2A Endpoint + Host Agent

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Folder Structure](#2-folder-structure)
3. [Phase-by-Phase Implementation](#3-phase-by-phase-implementation)
   - [Phase 0 — Setup & Config](#phase-0--setup--config)
   - [Phase 1 — Shared Models & LLM Client](#phase-1--shared-models--llm-client)
   - [Phase 2 — MCP Tool Layer](#phase-2--mcp-tool-layer)
   - [Phase 3 — Specialized Agent](#phase-3--specialized-agent)
   - [Phase 4 — A2A Endpoint](#phase-4--a2a-endpoint)
   - [Phase 5 — Host Agent / Orchestrator](#phase-5--host-agent--orchestrator)
   - [Phase 6 — Docker & Deployment](#phase-6--docker--deployment)
   - [Phase 7 — Demo Scenarios](#phase-7--demo-scenarios)
4. [API Reference](#4-api-reference)
5. [Environment Variables](#5-environment-variables)
6. [Grading Checklist](#6-grading-checklist)

---

## 1. Project Overview

```
User Query
    │
    ▼
Host Agent  (:8000)
    │
    ├──► Research Agent  (:8001)   ← your teammate's agent (or yours)
    ├──► Solution Agent  (:8002)   ← your teammate's agent (or yours)
    └──► Experiment Agent (:8003)  ← your specialized agent
```

Each agent:
- Runs an LLM with prompt engineering
- Exposes **MCP tools** (≥ 3, recommended 5–10)
- Is discoverable + callable via **A2A** REST endpoints
- Returns **structured JSON** responses

---

## 2. Folder Structure

```
multi-agent-research/
│
├── host-agent/
│   ├── main.py              # FastAPI app, port 8000
│   ├── orchestrator.py      # task decomposition + aggregation logic
│   ├── router.py            # decides which agents to call
│   └── prompts/
│       └── orchestrator.txt
│
├── research-agent/          # Member A's specialization (example)
│   ├── main.py              # FastAPI app, port 8001
│   ├── agent.py             # LLM invocation + tool selection
│   ├── tools/
│   │   ├── paper_search.py
│   │   ├── summarizer.py
│   │   └── gap_analysis.py
│   └── prompts/
│       └── agent.txt
│
├── solution-agent/          # Member B's specialization (example)
│   ├── main.py              # FastAPI app, port 8002
│   └── tools/
│       ├── dataset_finder.py
│       ├── architecture.py
│       └── recommender.py
│
├── experiment-agent/        # Member C's specialization (example)
│   ├── main.py              # FastAPI app, port 8003
│   └── tools/
│       ├── planner.py
│       ├── metrics.py
│       └── hyperparams.py
│
├── shared/
│   ├── models.py            # Pydantic schemas (AgentRequest, AgentResponse)
│   ├── config.py            # Port map, agent URLs, env vars
│   └── llm.py              # LLM client wrapper (Gemini / NVIDIA)
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 3. Phase-by-Phase Implementation

---

### Phase 0 — Setup & Config

**Goal:** get the repo scaffolded and dependencies installed.

#### `requirements.txt`
```
fastapi
uvicorn
httpx
pydantic
python-dotenv
google-generativeai       # or openai-compatible for NVIDIA
arxiv                     # for paper search
requests
```

#### `shared/config.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

AGENT_URLS = {
    "research":   os.getenv("RESEARCH_AGENT_URL",   "http://localhost:8001"),
    "solution":   os.getenv("SOLUTION_AGENT_URL",   "http://localhost:8002"),
    "experiment": os.getenv("EXPERIMENT_AGENT_URL", "http://localhost:8003"),
}
```

---

### Phase 1 — Shared Models & LLM Client

**Goal:** define the data contract used by all agents.

#### `shared/models.py`
```python
from pydantic import BaseModel
from typing import Any

class AgentRequest(BaseModel):
    query: str
    context: dict = {}

class AgentResponse(BaseModel):
    agent: str
    result: dict[str, Any]
    status: str = "success"
```

#### `shared/llm.py`
```python
import google.generativeai as genai
from shared.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def call_llm(system_prompt: str, user_prompt: str, model: str = "gemini-1.5-flash") -> str:
    """
    Call Gemini (or swap for NVIDIA endpoint if rate-limited).
    Returns the text response string.
    """
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    response = genai.GenerativeModel(model).generate_content(full_prompt)
    return response.text

# NVIDIA fallback (openai-compatible):
# from openai import OpenAI
# client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
# response = client.chat.completions.create(model="google/gemma-3n-e4b-it", messages=[...])
```

---

### Phase 2 — MCP Tool Layer

**Goal:** implement ≥ 5 tools per agent and register them in a tool registry.

#### Pattern: Tool Registry
```python
# Inside any agent's tools/__init__.py

TOOLS = {
    "paper_search":   search_papers,
    "paper_summary":  summarize_paper,
    "research_gap":   analyze_gaps,
    "citation":       generate_citation,
    "experiment_plan": plan_experiment,
}

def execute_tool(name: str, **kwargs) -> dict:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name](**kwargs)
```

#### Common Tools (implement in every agent)

| Tool | Function Signature | Output Keys |
|------|--------------------|-------------|
| Paper Search | `search_papers(query: str) -> list` | `title, authors, year, abstract` |
| Paper Summary | `summarize_paper(text: str) -> dict` | `summary, key_contributions, limitations` |
| Research Gap Analysis | `analyze_gaps(papers: list) -> dict` | `existing_approaches, gaps` |
| Citation Generator | `generate_citation(paper: dict) -> str` | APA/IEEE string |
| Experiment Planner | `plan_experiment(problem: str) -> dict` | `datasets, models, metrics, strategy` |

#### Example: `tools/paper_search.py`
```python
import arxiv

def search_papers(query: str, max_results: int = 5) -> list[dict]:
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results,
                          sort_by=arxiv.SortCriterion.Relevance)
    results = []
    for paper in client.results(search):
        results.append({
            "title":    paper.title,
            "authors":  [str(a) for a in paper.authors],
            "year":     paper.published.year,
            "abstract": paper.summary[:300],
            "url":      paper.entry_id,
        })
    return results
```

#### Agent-Specific Tools

**Computer Vision Agent:**
- `find_cv_datasets(topic)` → COCO, ImageNet, Open Images
- `recommend_cv_models(problem)` → CNNs, ViT, SAM
- `benchmark_search(task)` → SOTA leaderboard
- `eval_metric_advisor(task)` → IoU, mAP, Dice
- `architecture_comparison(candidates)` → comparison table

**NLP Agent:**
- `find_nlp_datasets(topic)` → HuggingFace, GLUE, SQuAD
- `optimize_prompt(draft)` → improved prompt
- `rag_design(problem)` → chunking + embedding + retrieval
- `llm_benchmark(task)` → compare LLMs
- `eval_metric_advisor(task)` → BLEU, ROUGE, F1

**ML Agent:**
- `recommend_models(problem)` → sklearn / boosting / neural
- `feature_engineering(dataset_info)` → transformations
- `experiment_design(problem)` → baselines + ablations
- `hyperparameter_advice(model)` → tuning ranges
- `explainability_advisor(model)` → SHAP / LIME

---

### Phase 3 — Specialized Agent

**Goal:** wire LLM + tools into a single agent that selects and runs tools based on the query.

#### `<your-agent>/agent.py`
```python
import json
from shared.llm import call_llm
from tools import TOOLS, execute_tool

SYSTEM_PROMPT = """
You are an expert [Computer Vision / NLP / Machine Learning] research agent.
Given a research query, choose the most relevant tools from this list:
{tool_list}

Respond ONLY with valid JSON in this format:
{{
  "selected_tools": ["tool_name_1", "tool_name_2"],
  "reasoning": "why these tools"
}}
"""

def run_agent(query: str) -> dict:
    tool_list = list(TOOLS.keys())
    
    # Step 1: LLM selects tools
    decision_raw = call_llm(
        system_prompt=SYSTEM_PROMPT.format(tool_list=tool_list),
        user_prompt=query
    )
    decision = json.loads(decision_raw)
    
    # Step 2: Execute selected tools
    results = {}
    for tool_name in decision["selected_tools"]:
        results[tool_name] = execute_tool(tool_name, query=query)
    
    # Step 3: LLM synthesizes final answer
    synthesis_prompt = f"""
    Query: {query}
    Tool Results: {json.dumps(results, indent=2)}
    
    Synthesize a structured research response with:
    - papers, datasets, models, recommendations, evaluation_plan
    Return ONLY valid JSON.
    """
    final_raw = call_llm(system_prompt="You are a research synthesizer.", user_prompt=synthesis_prompt)
    return json.loads(final_raw)
```

---

### Phase 4 — A2A Endpoint

**Goal:** expose the agent as a discoverable REST service.

#### `<your-agent>/main.py`
```python
from fastapi import FastAPI
from shared.models import AgentRequest, AgentResponse
from agent import run_agent

app = FastAPI(title="[Your] Research Agent")

CAPABILITIES = {
    "name": "Experiment Research Agent",          # change per agent
    "description": "Specializes in experiment design and evaluation strategy",
    "port": 8003,
    "tasks": [
        "experiment_planning",
        "metric_recommendation",
        "hyperparameter_advice",
        "paper_search",
        "research_gap_analysis",
    ]
}

@app.get("/capabilities")
def capabilities():
    return CAPABILITIES

@app.post("/research", response_model=AgentResponse)
def research(req: AgentRequest):
    result = run_agent(req.query)
    return AgentResponse(agent=CAPABILITIES["name"], result=result)

@app.get("/health")
def health():
    return {"status": "ok", "agent": CAPABILITIES["name"]}

# Run: uvicorn main:app --host 0.0.0.0 --port 8003
```

---

### Phase 5 — Host Agent / Orchestrator

**Goal:** receive the user query, decompose it, call all three agents, aggregate results.

#### `host-agent/orchestrator.py`
```python
import httpx
import json
from shared.llm import call_llm
from shared.config import AGENT_URLS

DECOMPOSE_PROMPT = """
You are a research orchestrator. Break the following query into three subtasks,
one for each agent: research, solution, experiment.

Respond ONLY with valid JSON:
{{
  "research_task": "...",
  "solution_task": "...",
  "experiment_task": "..."
}}

Query: {query}
"""

async def orchestrate(query: str) -> dict:
    # Step 1: Decompose
    decomposed_raw = call_llm("You are an orchestrator.", DECOMPOSE_PROMPT.format(query=query))
    tasks = json.loads(decomposed_raw)

    # Step 2: Call all agents in parallel
    async with httpx.AsyncClient(timeout=60) as client:
        responses = {}
        for agent_name, task_key in [
            ("research",   "research_task"),
            ("solution",   "solution_task"),
            ("experiment", "experiment_task"),
        ]:
            url = f"{AGENT_URLS[agent_name]}/research"
            payload = {"query": tasks[task_key]}
            try:
                r = await client.post(url, json=payload)
                responses[agent_name] = r.json()
            except Exception as e:
                responses[agent_name] = {"error": str(e)}

    # Step 3: Aggregate
    agg_prompt = f"""
    Combine these three agent responses into a single research report.
    Research: {json.dumps(responses.get('research', {}))}
    Solution: {json.dumps(responses.get('solution', {}))}
    Experiment: {json.dumps(responses.get('experiment', {}))}
    Return ONLY valid JSON with keys: literature_review, datasets, models, evaluation_plan, prototype_guidance
    """
    final_raw = call_llm("You are a research report writer.", agg_prompt)
    return json.loads(final_raw)
```

#### `host-agent/main.py`
```python
from fastapi import FastAPI
from shared.models import AgentRequest
from orchestrator import orchestrate

app = FastAPI(title="Host Agent / Orchestrator")

@app.post("/research")
async def research(req: AgentRequest):
    result = await orchestrate(req.query)
    return {"query": req.query, "report": result}

@app.get("/health")
def health():
    return {"status": "ok", "agent": "Host Orchestrator"}

# Run: uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### Phase 6 — Docker & Deployment

**Goal:** run all 4 services with a single command.

#### `docker-compose.yml`

```yaml
version: "3.9"

services:
  host-agent:
    build: ../host-agent
    ports:
      - "8000:8000"
    env_file: ../.env
    depends_on:
      - research-agent
      - solution-agent
      - experiment-agent

  research-agent:
    build: ../research-agent
    ports:
      - "8001:8001"
    env_file: ../.env

  solution-agent:
    build: ../solution-agent
    ports:
      - "8002:8002"
    env_file: ../.env

  experiment-agent:
    build: ../experiment-agent
    ports:
      - "8003:8003"
    env_file: ../.env
```

#### `Dockerfile` (same template for every agent)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```
> Change the port in CMD per agent.

**Start everything:**
```bash
docker-compose up --build
```

---

### Phase 7 — Demo Scenarios

Test all three required scenarios by hitting the Host Agent:

#### Scenario 1 — Research Proposal
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a research proposal for crop disease detection"}'
```

#### Scenario 2 — Architecture Recommendation
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Recommend an architecture for multimodal fake news detection"}'
```

#### Scenario 3 — End-to-End POC
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a proof of concept for medical image diagnosis"}'
```

**Expected output structure:**
```json
{
  "literature_review": { "papers": [], "summary": "", "gaps": [] },
  "datasets":          [],
  "models":            [],
  "evaluation_plan":   { "metrics": [], "strategy": "" },
  "prototype_guidance": ""
}
```

---

## 4. API Reference

| Agent | Port | Endpoints |
|-------|------|-----------|
| Host | 8000 | `POST /research` · `GET /health` |
| Research | 8001 | `GET /capabilities` · `POST /research` · `GET /health` |
| Solution | 8002 | `GET /capabilities` · `POST /solution` · `GET /health` |
| Experiment | 8003 | `GET /capabilities` · `POST /experiment` · `GET /health` |

Interactive docs at `http://localhost:<port>/docs` (FastAPI auto-generates Swagger UI).

---

## 5. Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here          # fallback if Gemini rate-limited

RESEARCH_AGENT_URL=http://research-agent:8001
SOLUTION_AGENT_URL=http://solution-agent:8002
EXPERIMENT_AGENT_URL=http://experiment-agent:8003
```

> In Docker Compose, service names resolve as hostnames. Use `http://localhost:800X` when running locally without Docker.

---

## 6. Grading Checklist

| Requirement | Where | Status |
|-------------|-------|--------|
| Specialized agent with domain expertise | `<agent>/agent.py` | ☐ |
| LLM used with prompt engineering | `shared/llm.py` + prompts | ☐ |
| MCP tool layer (≥ 3, target 5–10) | `<agent>/tools/` | ☐ |
| Structured JSON responses | `shared/models.py` | ☐ |
| `GET /capabilities` endpoint | `<agent>/main.py` | ☐ |
| `POST /research` endpoint | `<agent>/main.py` | ☐ |
| `GET /health` endpoint | `<agent>/main.py` | ☐ |
| A2A: agent accepts remote requests | tested via curl | ☐ |
| Host Agent orchestrates 3 agents | `host-agent/orchestrator.py` | ☐ |
| Task decomposition logic | `orchestrator.py` | ☐ |
| Response aggregation into final report | `orchestrator.py` | ☐ |
| Scenario 1: crop disease detection | demo curl | ☐ |
| Scenario 2: fake news detection | demo curl | ☐ |
| Scenario 3: medical image diagnosis | demo curl | ☐ |
| Docker Compose deployment | `docker-compose.yml` | ☐ |
| Documentation / README | `README.md` | ☐ |

### Bonus (if time permits)
- [ ] Agent memory with SQLite
- [ ] RAG integration (vector DB + embeddings)
- [ ] Multi-agent debate (agents critique each other)
- [ ] Autonomous research proposal generation
- [ ] Code generation for POC implementations
- [ ] Dynamic agent discovery (host auto-discovers agents)

---

*Generated for the Multi-Agent Research Ecosystem assignment. Each phase builds on the previous one — complete them in order.*
