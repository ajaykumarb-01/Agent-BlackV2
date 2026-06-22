from .paper_search import search_papers
from .summarizer import summarize_paper
from .gap_analysis import analyze_gaps
from .nlp_datasets import find_nlp_datasets
from .rag_design import rag_design
from .llm_benchmark import llm_benchmark
from .citation_generator import citation_generator
from .prompt_optimizer import prompt_optimizer
from .information_extraction import information_extraction
from .eval_metrics import eval_metric_advisor_nlp
from .solution_recommendation import solution_recommendation
from .prototype_guidance import prototype_guidance
from .experiment_planner import experiment_planner

TOOLS = {
    "search_papers": search_papers,
    "summarize_paper": summarize_paper,
    "analyze_gaps": analyze_gaps,
    "find_nlp_datasets": find_nlp_datasets,
    "rag_design": rag_design,
    "llm_benchmark": llm_benchmark,
    "citation_generator": citation_generator,
    "prompt_optimizer": prompt_optimizer,
    "information_extraction": information_extraction,
    "eval_metric_advisor": eval_metric_advisor_nlp,
    "solution_recommendation": solution_recommendation,
    "prototype_guidance": prototype_guidance,
    "experiment_planner": experiment_planner,
}

TASKS = list(TOOLS.keys())


def _schema(description: str, properties: dict, required: list | None = None) -> dict:
    schema = {"type": "object", "description": description, "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _query_prop(description: str = "Research query or keyword phrase") -> dict:
    return {"type": "string", "description": description, "minLength": 1}


TOOL_SCHEMAS = {
    "search_papers": _schema(
        "Search academic papers across CrossRef, Semantic Scholar, and arXiv; failures are returned as partial errors.",
        {
            "query": _query_prop(),
            "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "year": {"type": "string", "description": "Optional year or year range, for example 2024 or 2020-2024"},
            "domain": {"type": "string", "description": "Optional NLP domain filter, for example QA, summarization, RAG"},
            "source": {"type": "string", "description": "Comma-separated sources: all, crossref, semantic_scholar, arxiv", "default": "all"},
        },
        ["query"],
    ),
    "summarize_paper": _schema(
        "Summarize a paper from supplied text or by resolving a title/query through CrossRef and arXiv.",
        {
            "query": _query_prop("Paper title, DOI, arXiv query, or abstract text"),
            "text": {"type": "string", "description": "Optional full paper text or abstract to summarize"},
            "max_words": {"type": "integer", "minimum": 50, "maximum": 1000, "default": 300},
        },
        ["query"],
    ),
    "analyze_gaps": _schema(
        "Analyze NLP research gaps from a query and optional paper context.",
        {
            "query": _query_prop(),
            "papers": {"type": "array", "items": {"type": "object"}, "description": "Optional paper records from search_papers"},
            "focus": {"type": "string", "description": "Optional gap-analysis focus, for example methodology, datasets, evaluation"},
        },
        ["query"],
    ),
    "find_nlp_datasets": _schema(
        "Find real NLP datasets from Hugging Face Datasets, Kaggle, and Papers With Code.",
        {
            "query": _query_prop("Dataset topic or keyword"),
            "topic": {"type": "string", "description": "Dataset topic, for example question answering, summarization"},
            "domain": {"type": "string", "description": "NLP domain, for example QA, NER, dialogue, classification", "default": "nlp"},
            "task": {"type": "string", "description": "Dataset task, for example extractive-qa, text-classification"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "sources": {"type": "array", "items": {"type": "string", "enum": ["huggingface", "kaggle", "paperswithcode"]}, "default": ["huggingface", "kaggle", "paperswithcode"]},
        },
        ["query"],
    ),
    "rag_design": _schema(
        "Design a RAG architecture for an NLP use case.",
        {
            "query": _query_prop("RAG design request"),
            "problem": {"type": "string", "description": "Specific use case, for example legal Q&A, medical chatbot"},
            "data_type": {"type": "string", "description": "Source data type, for example PDFs, HTML, code, internal docs"},
            "scale": {"type": "string", "description": "Corpus size bucket, for example small/medium/large/enterprise"},
            "constraints": {"type": "object", "description": "Optional constraints such as latency, hosting, accuracy"},
        },
        ["query"],
    ),
    "llm_benchmark": _schema(
        "Compare LLMs for a specific NLP task with cost and capability guidance.",
        {
            "query": _query_prop("LLM comparison request"),
            "task": {"type": "string", "description": "NLP task, for example summarization, code generation, reasoning"},
            "constraints": {"type": "object", "description": "Optional constraints such as context length, cost, latency, hosting"},
        },
        ["query"],
    ),
    "citation_generator": _schema(
        "Generate formatted citations from DOI, arXiv, Semantic Scholar, CrossRef, or supplied metadata.",
        {
            "query": {"type": "string", "description": "Fallback paper title or bibliographic query"},
            "title": {"type": "string", "description": "Paper title"},
            "doi": {"type": "string", "description": "DOI, for example 10.1109/CVPR.2020.12345"},
            "authors": {"type": "string", "description": "Comma-separated authors"},
            "year": {"type": ["integer", "string"], "description": "Publication year"},
            "venue": {"type": "string", "description": "Journal, conference, or venue"},
            "url": {"type": "string", "description": "Paper URL"},
            "arxiv_id": {"type": "string", "description": "arXiv ID, for example 2401.12345"},
            "source": {"type": "string", "description": "auto, crossref, semantic_scholar, or arxiv", "default": "auto"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
        },
    ),
    "prompt_optimizer": _schema(
        "Optimize a prompt for an NLP task with reasoning.",
        {
            "query": _query_prop("Prompt optimization request"),
            "task": {"type": "string", "description": "NLP task the prompt is targeting"},
            "prompt_text": {"type": "string", "description": "Current prompt text to optimize"},
            "model": {"type": "string", "description": "Target model family, for example GPT-4, Claude, Gemini"},
        },
        ["query"],
    ),
    "information_extraction": _schema(
        "Extract structured information (entities, relations, key concepts) from text.",
        {
            "query": _query_prop("Information extraction request"),
            "text": {"type": "string", "description": "Text to extract from"},
            "schema": {"type": "object", "description": "Optional target schema describing fields and types"},
        },
        ["query"],
    ),
    "eval_metric_advisor": _schema(
        "Recommend evaluation metrics for an NLP task.",
        {
            "query": _query_prop("Evaluation metric request"),
            "task": {"type": "string", "description": "NLP task, for example QA, summarization, NER"},
            "data_type": {"type": "string", "description": "Data characteristics, for example multilingual, long-form, multi-label"},
        },
        ["query"],
    ),
    "solution_recommendation": _schema(
        "Recommend practical NLP solution approaches and an implementation roadmap.",
        {
            "query": _query_prop("Solution recommendation request"),
            "problem": {"type": "string", "description": "Specific problem statement"},
            "constraints": {"type": "object", "description": "Optional constraints such as compute, latency, data availability"},
        },
        ["query"],
    ),
    "prototype_guidance": _schema(
        "Provide prototype development guidance for an NLP use case.",
        {
            "query": _query_prop("Prototype guidance request"),
            "problem": {"type": "string", "description": "Specific use case"},
            "stack": {"type": "string", "description": "Preferred stack, for example LangChain, LlamaIndex, Haystack"},
        },
        ["query"],
    ),
    "experiment_planner": _schema(
        "Design an experiment plan for an NLP research problem.",
        {
            "query": _query_prop("Experiment planning request"),
            "problem": {"type": "string", "description": "Research problem"},
            "datasets": {"type": "array", "items": {"type": "string"}, "description": "Candidate datasets"},
            "baselines": {"type": "array", "items": {"type": "string"}, "description": "Candidate baselines"},
        },
        ["query"],
    ),
}


def execute_tool(name: str, query: str = "", **kwargs) -> dict:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name](query=query, **kwargs)


from fastmcp import FastMCP
from shared.mcp import create_mcp_server


def build_mcp_server(agent_name: str = "Solution Agent") -> FastMCP:
    return create_mcp_server(agent_name, TOOLS, TOOL_SCHEMAS)
