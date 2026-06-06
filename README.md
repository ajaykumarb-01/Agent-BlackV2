# Multi-Agent Research Ecosystem

A multi-agent research assistant system using FastAPI, LLMs (Gemini), and MCP/A2A patterns.

## Architecture

```
User Query
    │
    ▼
Host Agent  (:8000)  — Orchestrator
    │
    ├──► Research Agent  (:8001)  — Computer Vision specialist
    ├──► Solution Agent  (:8002)  — NLP/Architecture specialist
    └──► Experiment Agent (:8003) — ML Experiment specialist
```

## Agents

| Agent | Port | Specialization | Tools |
|-------|------|----------------|-------|
| Host | 8000 | Orchestrator, task decomposition, aggregation | LLM decomposition + synthesis |
| Research | 8001 | Computer Vision | paper search, summarization, gap analysis, CV datasets, CV models |
| Solution | 8002 | NLP / Architecture | paper search, summarization, NLP datasets, RAG design, LLM benchmarks |
| Experiment | 8003 | ML Experiments | paper search, experiment planner, metrics, hyperparameters, model selection |

## Quick Start

### Local
```bash
pip install -r requirements.txt

# Terminal 1: Research Agent
uvicorn research-agent.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Solution Agent
uvicorn solution-agent.main:app --host 0.0.0.0 --port 8002

# Terminal 3: Experiment Agent
uvicorn experiment-agent.main:app --host 0.0.0.0 --port 8003

# Terminal 4: Host Agent
uvicorn host-agent.main:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker-compose up --build
```

## API Endpoints

### Host Agent (port 8000)
- `POST /research` — Submit research query, returns aggregated report
- `GET /health` — Health check
- `GET /` — Service info

### Agent Endpoints (ports 8001-8003)
- `GET /capabilities` — List agent capabilities
- `POST /research` (8001) / `POST /solution` (8002) / `POST /experiment` (8003) — Execute agent
- `GET /health` — Health check

## Demo Scenarios

```bash
# Scenario 1: Crop Disease Detection
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a research proposal for crop disease detection"}'

# Scenario 2: Multimodal Fake News Detection
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Recommend an architecture for multimodal fake news detection"}'

# Scenario 3: Medical Image Diagnosis
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a proof of concept for medical image diagnosis"}'
```

## Environment Variables

Copy `.env.example` to `.env` and set:
```
GEMINI_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here
```

## Project Structure

```
multi-agent-research/
├── host-agent/           # Orchestrator (port 8000)
├── research-agent/       # CV Research (port 8001)
├── solution-agent/       # NLP Solutions (port 8002)
├── experiment-agent/     # ML Experiments (port 8003)
├── shared/               # Common models, config, LLM client
├── docker-compose.yml
├── requirements.txt
└── .env
```
