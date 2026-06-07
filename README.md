# Agent Black

A collaborative multi-agent research assistant ecosystem built with **FastAPI**, **LLMs** (Gemini / OpenAI / Anthropic), **MCP** (Model Context Protocol), and **A2A** (Agent-to-Agent) communication.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agents](#agents)
  - [Host Agent (Orchestrator)](#host-agent-orchestrator)
  - [CV Research Agent](#cv-research-agent)
  - [NLP Solution Agent](#nlp-solution-agent)
  - [ML Experiment Agent](#ml-experiment-agent)
- [MCP Tools](#mcp-tools)
- [A2A Protocol](#a2a-protocol)
- [Orchestrator Pipeline](#orchestrator-pipeline)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [API Reference](#api-reference)
  - [Host Agent Endpoints](#host-agent-endpoints-port-8000)
  - [CV Research Agent Endpoints](#cv-research-agent-endpoints-port-8001)
  - [NLP Solution Agent Endpoints](#nlp-solution-agent-endpoints-port-8002)
  - [ML Experiment Agent Endpoints](#ml-experiment-agent-endpoints-port-8003)
- [Demo Scenarios](#demo-scenarios)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)

---

## Overview

Agent Black is a multi-agent system where a **Host Agent** orchestrates three **specialized research agents** to solve AI/ML/CV/NLP research queries. Each agent is an independent FastAPI service with its own MCP tool server and A2A endpoint.

**Key features:**
- Research-relevance gating — rejects non-research queries with a helpful message
- LLM-driven task decomposition and agent selection
- Concurrent agent dispatch via `asyncio.gather`
- MCP tool layer (JSON-RPC 2.0) on every agent
- A2A protocol for cross-agent communication
- Multi-provider LLM support (Gemini, OpenAI, Anthropic) with automatic retry
- Docker containerization

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  Host Agent  (:8000)  — Orchestrator    │
│                                         │
│  Step 0: Research-relevance gate        │
│  Step 1: Agent selection (LLM)          │
│  Step 2: Task decomposition (LLM)       │
│  Step 3: Concurrent dispatch             │
│  Step 4: Result aggregation (LLM)       │
└────────┬──────────┬──────────┬──────────┘
         │          │          │
         ▼          ▼          ▼
┌────────────┐ ┌────────────┐ ┌────────────────┐
│ Research   │ │ Solution   │ │ Experiment     │
│ Agent      │ │ Agent      │ │ Agent          │
│ (:8001)    │ │ (:8002)    │ │ (:8003)        │
│            │ │            │ │                │
│ CV         │ │ NLP        │ │ ML             │
│ Specialist │ │ Specialist │ │ Specialist     │
│            │ │            │ │                │
│ [13 MCP]   │ │ [13 MCP]   │ │ [13 MCP]       │
│ [A2A]      │ │ [A2A]      │ │ [A2A]          │
└────────────┘ └────────────┘ └────────────────┘
```

---

## Agents

### Host Agent (Orchestrator)

| Property | Value |
|----------|-------|
| Port | `8000` |
| Role | Orchestrator — decomposes queries, selects agents, aggregates results |
| LLM | Yes — for classification, decomposition, and synthesis |
| MCP Tools | None (pure orchestrator) |
| A2A | Yes |

**Responsibilities:**
1. **Research-relevance gate** — keyword check + LLM classifier rejects non-research queries
2. **Agent selection** — LLM decides which of the 3 agents are relevant
3. **Task decomposition** — LLM breaks the query into domain-specific sub-tasks
4. **Concurrent dispatch** — sends sub-tasks to selected agents in parallel
5. **Result aggregation** — LLM synthesizes all agent outputs into a unified report

### CV Research Agent

| Property | Value |
|----------|-------|
| Port | `8001` |
| Domain | Computer Vision |
| MCP Tools | 13 |
| A2A | Yes |

**Specializations:** Image classification, object detection, segmentation, vision transformers, vision-language models, medical imaging, video analytics.

### NLP Solution Agent

| Property | Value |
|----------|-------|
| Port | `8002` |
| Domain | NLP / Solution Architecture |
| MCP Tools | 13 |
| A2A | Yes |

**Specializations:** LLMs, RAG, prompt engineering, text classification, summarization, conversational AI, information extraction.

### ML Experiment Agent

| Property | Value |
|----------|-------|
| Port | `8003` |
| Domain | Machine Learning Experiments |
| MCP Tools | 13 |
| A2A | Yes |

**Specializations:** Classical ML, model selection, feature engineering, time series, hyperparameter tuning, evaluation strategies, experiment design.

---

## MCP Tools

Each agent exposes its tools via an MCP server using **JSON-RPC 2.0** over HTTP (`POST /mcp`).

### Common Tools (all agents)

| Tool | Description |
|------|-------------|
| `search_papers` | Search academic literature (CrossRef + Semantic Scholar + arXiv) |
| `summarize_paper` | LLM-powered paper summarization (summary, contributions, limitations) |
| `analyze_gaps` | Identify research gaps and unexplored opportunities |
| `citation_generator` | Generate references in BibTeX, APA, MLA, IEEE formats |
| `solution_recommendation` | Recommend practical solutions with implementation roadmap |
| `prototype_guidance` | MVP pipeline, pitfalls, and next steps |
| `experiment_planner` | Design experiment plans (datasets, baselines, ablations, metrics) |

### CV Research Agent — Additional Tools

| Tool | Description |
|------|-------------|
| `find_cv_datasets` | Recommend COCO, ImageNet, Open Images, medical datasets |
| `recommend_cv_models` | Recommend CNNs, ViTs, segmentation models |
| `benchmark_search` | Find state-of-the-art benchmarks for CV tasks |
| `eval_metric_advisor` | Recommend IoU, mAP, Dice Score, accuracy |
| `architecture_comparison` | Compare candidate CV architectures |
| `synthetic_data_strategy` | Recommend augmentation and synthetic data techniques |

### NLP Solution Agent — Additional Tools

| Tool | Description |
|------|-------------|
| `find_nlp_datasets` | Recommend HuggingFace, GLUE, SuperGLUE, SQuAD datasets |
| `rag_design` | Design RAG architecture (chunking, embedding, retrieval) |
| `llm_benchmark` | Compare LLMs for specific tasks |
| `eval_metric_advisor` | Recommend BLEU, ROUGE, F1, Exact Match |
| `prompt_optimizer` | Generate optimized prompts |
| `information_extraction` | Extract entities, relationships, key concepts |

### ML Experiment Agent — Additional Tools

| Tool | Description |
|------|-------------|
| `recommend_models` | Recommend suitable ML algorithms |
| `feature_engineering_advisor` | Suggest feature transformations |
| `hyperparameter_advice` | Suggest tuning ranges (LR, batch size, optimizer) |
| `eval_metric_advisor` | Recommend task-appropriate metrics |
| `benchmark_search` | Find state-of-the-art ML benchmarks |
| `model_explainability_advisor` | Recommend SHAP, LIME, feature importance |
| `time_series_strategy` | Recommend forecasting approaches |

---

## A2A Protocol

Every agent supports Agent-to-Agent communication via JSON-RPC 2.0.

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /.well-known/agent-card` | Returns agent card (name, description, capabilities, skills) |
| `POST /a2a` | Accepts `a2a/agent-card` and `a2a/sendTask` methods |

### Agent Card Format

```json
{
  "name": "Computer Vision Research Agent",
  "description": "Specializes in computer vision research...",
  "url": "http://localhost:8001",
  "version": "1.0.0",
  "capabilities": ["paper_search", "paper_summarization", ...],
  "skills": [{"id": "paper_search", "name": "Paper Search", ...}],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

### Task Request

```json
{
  "jsonrpc": "2.0",
  "method": "a2a/sendTask",
  "params": {"query": "Find datasets for medical image segmentation"},
  "id": "1"
}
```

### Task Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "1",
    "status": {"state": "completed"},
    "artifacts": [{"parts": [{"text": "{...structured response...}"}]}]
  },
  "id": "1"
}
```

---

## Orchestrator Pipeline

The Host Agent runs a 5-step pipeline for every query:

```
Step 0: Research-relevance gate
        ├─ Keyword fast-path (30+ AI/ML/CV/NLP keywords)
        └─ LLM fallback classifier
        └─ Reject → return {error: "not_research_query", supported_topics: [...]}

Step 1: Agent selection (LLM)
        └─ Decides which of research/solution/experiment agents are needed

Step 2: Task decomposition (LLM)
        └─ Breaks query into domain-specific sub-tasks

Step 3: Concurrent dispatch
        └─ HTTP POST to selected agents in parallel (asyncio.gather)

Step 4: Result aggregation (LLM)
        └─ Synthesizes all agent outputs into:
           {literature_review, datasets, models, evaluation_plan, prototype_guidance}
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup)
- An LLM API key (Gemini, OpenAI, or Anthropic)

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/hareesh08/Agent-BlackV2.git
cd Agent-BlackV2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure LLM provider (edit data/agent_black.db or use the setup API)
#    Or set via environment before starting:
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here

# 4. Start all agents
python start.py
```

This starts:
- Research Agent → `http://localhost:8001`
- Solution Agent → `http://localhost:8002`
- Experiment Agent → `http://localhost:8003`
- Host Agent / Control Panel → `http://localhost:8000`

### Docker Setup

```bash
# Build and start all containers
docker-compose up --build

# Stop all containers
docker-compose down
```

---

## API Reference

### Host Agent Endpoints (port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info and available agents |
| `GET` | `/health` | Health check |
| `GET` | `/.well-known/agent-card` | A2A agent card |
| `POST` | `/research` | Submit research query → aggregated report |
| `POST` | `/a2a` | A2A protocol endpoint |

### CV Research Agent Endpoints (port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/capabilities` | Agent capabilities and task list |
| `GET` | `/.well-known/agent-card` | A2A agent card |
| `GET` | `/tools` | List all registered MCP tools |
| `GET` | `/health` | Health check |
| `POST` | `/research` | Execute CV research agent |
| `POST` | `/mcp` | MCP JSON-RPC endpoint (`tools/list`, `tools/call`) |
| `POST` | `/a2a` | A2A protocol endpoint |

### NLP Solution Agent Endpoints (port 8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/capabilities` | Agent capabilities and task list |
| `GET` | `/.well-known/agent-card` | A2A agent card |
| `GET` | `/tools` | List all registered MCP tools |
| `GET` | `/health` | Health check |
| `POST` | `/solution` | Execute NLP solution agent |
| `POST` | `/mcp` | MCP JSON-RPC endpoint (`tools/list`, `tools/call`) |
| `POST` | `/a2a` | A2A protocol endpoint |

### ML Experiment Agent Endpoints (port 8003)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/capabilities` | Agent capabilities and task list |
| `GET` | `/.well-known/agent-card` | A2A agent card |
| `GET` | `/tools` | List all registered MCP tools |
| `GET` | `/health` | Health check |
| `POST` | `/experiment` | Execute ML experiment agent |
| `POST` | `/mcp` | MCP JSON-RPC endpoint (`tools/list`, `tools/call`) |
| `POST` | `/a2a` | A2A protocol endpoint |

---

## Demo Scenarios

### Scenario 1: Research Proposal Generation

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a research proposal for crop disease detection"}'
```

**Expected output:**
- Literature review of existing crop disease detection approaches
- Recommended datasets (PlantVillage, CropNet, etc.)
- Model recommendations (CNNs, ViTs, transfer learning)
- Evaluation strategy (accuracy, F1, confusion matrix)

### Scenario 2: Technology Recommendation

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Recommend an architecture for multimodal fake news detection"}'
```

**Expected output:**
- NLP recommendations (text embeddings, BERT variants)
- CV recommendations (image forensics, visual features)
- ML recommendations (fusion strategies, ensemble methods)

### Scenario 3: End-to-End Research Planning

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a proof of concept for medical image diagnosis"}'
```

**Expected output:**
- Relevant papers (medical imaging + deep learning)
- Datasets (ChestX-ray14, MIMIC-CXR, ISIC)
- Models (U-Net, ResNet, Vision Transformers)
- Experiment plan (baselines, ablations, compute estimate)
- Prototype guidance (MVP pipeline, common pitfalls)

### Scenario 4: Non-Rejection of Non-Research Query

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather today?"}'
```

**Expected output:**
```json
{
  "error": "not_research_query",
  "message": "This query does not appear to be related to AI/ML research...",
  "supported_topics": ["Research paper discovery and summarization", ...]
}
```

### Direct Agent Calls

```bash
# Call CV agent directly
curl -X POST http://localhost:8001/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Best segmentation model for medical imaging?"}'

# Call NLP agent directly
curl -X POST http://localhost:8002/solution \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a RAG pipeline for legal documents"}'

# Call ML agent directly
curl -X POST http://localhost:8003/experiment \
  -H "Content-Type: application/json" \
  -d '{"query": "Hyperparameter tuning strategy for XGBoost"}'
```

### MCP Tool Calls

```bash
# List available tools on CV agent
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Call a specific tool
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "search_papers", "arguments": {"query": "vision transformers for medical imaging"}}, "id": 2}'
```

### A2A Communication

```bash
# Discover agent capabilities
curl http://localhost:8001/.well-known/agent-card

# Send task via A2A protocol
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "a2a/sendTask", "params": {"query": "Recommend CV datasets for autonomous driving"}, "id": "1"}'
```

---

## Environment Variables

Configuration is stored in **SQLite** (`data/agent_black.db`). The `.env` file only holds infrastructure settings.

### `.env` (Infrastructure)

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Host agent port |
| `DOCKER_BUILDKIT` | `1` | Docker build optimization |
| `COMPOSE_PROJECT_NAME` | `agent-black` | Docker Compose project name |
| `VITE_API_URL` | `http://localhost:8000/api` | Frontend API URL |

### SQLite Settings (via API or DB)

| Key | Default | Description |
|-----|---------|-------------|
| `LLM_PROVIDER` | `gemini` | LLM provider: `gemini`, `openai`, or `anthropic` |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GEMINI_BASE_URL` | — | Custom Gemini endpoint (optional) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API base URL |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_BASE_URL` | — | Custom Anthropic endpoint (optional) |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Anthropic model name |
| `HOST_AGENT_URL` | `http://localhost:8000` | Host agent URL |
| `RESEARCH_AGENT_URL` | `http://localhost:8001` | CV research agent URL |
| `SOLUTION_AGENT_URL` | `http://localhost:8002` | NLP solution agent URL |
| `EXPERIMENT_AGENT_URL` | `http://localhost:8003` | ML experiment agent URL |

---

## Project Structure

```
Agent-BlackV2/
├── agents/
│   ├── host-agent/                  # Orchestrator (port 8000)
│   │   ├── main.py                  # FastAPI app + A2A + agent card
│   │   ├── orchestrator.py          # 5-step orchestration pipeline
│   │   ├── prompts/
│   │   │   ├── orchestrator.txt     # Task decomposition prompt
│   │   │   └── selection.txt        # Agent selection prompt
│   │   └── Dockerfile
│   │
│   ├── research-agent/              # CV specialist (port 8001)
│   │   ├── main.py                  # FastAPI app + MCP + A2A
│   │   ├── agent.py                 # LLM tool selection + execution
│   │   ├── prompts/
│   │   │   └── agent.txt            # Tool selection prompt
│   │   ├── tools/                   # 13 MCP tools
│   │   │   ├── paper_search.py      # CrossRef + Semantic Scholar + arXiv
│   │   │   ├── summarizer.py        # LLM paper summarization
│   │   │   ├── gap_analysis.py      # Research gap analysis
│   │   │   ├── cv_datasets.py       # CV dataset recommendation
│   │   │   ├── cv_models.py         # CV model recommendation
│   │   │   ├── benchmark_search.py  # SOTA benchmark search
│   │   │   ├── eval_advisor.py      # CV metric recommendation
│   │   │   ├── architecture_comparison.py
│   │   │   ├── synthetic_data.py    # Augmentation strategies
│   │   │   ├── citation_generator.py
│   │   │   ├── solution_recommendation.py
│   │   │   ├── prototype_guidance.py
│   │   │   └── experiment_planner.py
│   │   └── Dockerfile
│   │
│   ├── solution-agent/              # NLP specialist (port 8002)
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── prompts/
│   │   │   └── agent.txt
│   │   ├── tools/                   # 13 MCP tools
│   │   │   ├── paper_search.py
│   │   │   ├── summarizer.py
│   │   │   ├── gap_analysis.py
│   │   │   ├── nlp_datasets.py      # HuggingFace, GLUE, SQuAD
│   │   │   ├── rag_design.py        # RAG architecture design
│   │   │   ├── llm_benchmark.py     # LLM comparison
│   │   │   ├── eval_metrics.py      # BLEU, ROUGE, F1
│   │   │   ├── prompt_optimizer.py
│   │   │   ├── information_extraction.py
│   │   │   ├── citation_generator.py
│   │   │   ├── solution_recommendation.py
│   │   │   ├── prototype_guidance.py
│   │   │   └── experiment_planner.py
│   │   └── Dockerfile
│   │
│   └── experiment-agent/            # ML specialist (port 8003)
│       ├── main.py
│       ├── agent.py
│       ├── prompts/
│       │   └── agent.txt
│       ├── tools/                   # 13 MCP tools
│       │   ├── paper_search.py
│       │   ├── summarizer.py
│       │   ├── gap_analysis.py
│       │   ├── models.py            # ML model recommendation
│       │   ├── hyperparams.py       # Hyperparameter tuning
│       │   ├── metrics.py           # ML metric recommendation
│       │   ├── feature_engineering.py
│       │   ├── benchmark_search.py
│       │   ├── explainability.py    # SHAP, LIME
│       │   ├── time_series.py       # Forecasting strategies
│       │   ├── solution_recommendation.py
│       │   ├── prototype_guidance.py
│       │   └── experiment_planner.py
│       └── Dockerfile
│
├── shared/                          # Common modules
│   ├── config.py                    # SQLite-backed configuration
│   ├── llm.py                       # Multi-provider LLM client + retry
│   ├── mcp.py                       # MCP tool registry (JSON-RPC 2.0)
│   ├── a2a.py                       # A2A protocol (agent cards, tasks)
│   ├── models.py                    # Pydantic request/response models
│   ├── crossref.py                  # CrossRef academic API client
│   └── semantic_scholar.py          # Semantic Scholar API client
│
├── docker-compose.yml               # 4-service Docker setup
├── requirements.txt                 # Python dependencies
├── start.py                         # Local multi-process launcher
└── .env                             # Infrastructure config
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI + Uvicorn |
| LLM Providers | Google Gemini, OpenAI, Anthropic |
| Protocols | MCP (JSON-RPC 2.0), A2A (JSON-RPC 2.0) |
| Academic APIs | CrossRef, Semantic Scholar, arXiv |
| Validation | Pydantic v2 |
| HTTP Client | httpx (async) |
| Containerization | Docker + Docker Compose |
| Configuration | SQLite + python-dotenv |

---

## License

This project is for educational and research purposes.
