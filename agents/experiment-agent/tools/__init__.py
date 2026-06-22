from .paper_search import search_papers
from .summarizer import summarize_paper
from .gap_analysis import analyze_gaps
from .citation_generator import citation_generator
from .metrics import eval_metric_advisor
from .hyperparams import hyperparameter_advice
from .models import recommend_models
from .benchmark_search import benchmark_search_ml
from .feature_engineering import feature_engineering_advisor
from .explainability import model_explainability_advisor
from .time_series import time_series_strategy
from .solution_recommendation import solution_recommendation
from .prototype_guidance import prototype_guidance
from .experiment_planner import plan_experiment as experiment_planner

TOOLS = {
    "search_papers": search_papers,
    "summarize_paper": summarize_paper,
    "analyze_gaps": analyze_gaps,
    "citation_generator": citation_generator,
    "eval_metric_advisor": eval_metric_advisor,
    "hyperparameter_advice": hyperparameter_advice,
    "recommend_models": recommend_models,
    "benchmark_search": benchmark_search_ml,
    "feature_engineering_advisor": feature_engineering_advisor,
    "model_explainability_advisor": model_explainability_advisor,
    "time_series_strategy": time_series_strategy,
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
            "domain": {"type": "string", "description": "Optional ML domain filter, for example time series, tabular, NLP"},
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
        "Analyze ML research gaps from a query and optional paper context.",
        {
            "query": _query_prop(),
            "papers": {"type": "array", "items": {"type": "object"}, "description": "Optional paper records from search_papers"},
            "focus": {"type": "string", "description": "Optional gap-analysis focus, for example methodology, datasets, metrics"},
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
    "eval_metric_advisor": _schema(
        "Recommend evaluation metrics for an ML task.",
        {
            "query": _query_prop("Evaluation metric request"),
            "task": {"type": "string", "description": "ML task, for example classification, regression, ranking"},
            "domain": {"type": "string", "description": "ML domain, for example tabular, NLP, CV, time series"},
            "data_type": {"type": "string", "description": "Data characteristics, for example imbalanced, multilabel, sequential"},
        },
        ["query"],
    ),
    "hyperparameter_advice": _schema(
        "Recommend hyperparameter tuning strategies for a model family.",
        {
            "query": _query_prop("Hyperparameter request"),
            "model_type": {"type": "string", "description": "Model type, for example XGBoost, ResNet, BERT, LSTM"},
            "task": {"type": "string", "description": "ML task"},
            "dataset_size": {"type": "string", "description": "Dataset size bucket, for example small/medium/large"},
        },
        ["query"],
    ),
    "recommend_models": _schema(
        "Recommend ML models for a problem with optional constraints.",
        {
            "query": _query_prop("Model recommendation request"),
            "problem": {"type": "string", "description": "Specific ML problem statement"},
            "data_type": {"type": "string", "description": "Tabular, text, image, time series, graph, etc."},
            "constraints": {"type": "object", "description": "Optional constraints such as interpretability, latency, training cost"},
        },
        ["query"],
    ),
    "benchmark_search": _schema(
        "Search real Papers With Code benchmark/task data without hallucinating SOTA scores.",
        {
            "query": _query_prop("Benchmark task or dataset query"),
            "task": {"type": "string", "description": "Specific benchmark task, for example GLUE, ImageNet, MMLU"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "sources": {"type": "array", "items": {"type": "string", "enum": ["paperswithcode"]}, "default": ["paperswithcode"]},
        },
        ["query"],
    ),
    "feature_engineering_advisor": _schema(
        "Recommend feature engineering techniques for a data type.",
        {
            "query": _query_prop("Feature engineering request"),
            "data_type": {"type": "string", "description": "Data type, for example tabular, text, image, time series"},
            "task": {"type": "string", "description": "ML task"},
            "modality": {"type": "string", "description": "Optional modality hints, for example categorical-heavy, high-cardinality, missing-data"},
        },
        ["query"],
    ),
    "model_explainability_advisor": _schema(
        "Recommend model explainability and XAI methods.",
        {
            "query": _query_prop("Explainability request"),
            "model_type": {"type": "string", "description": "Model type, for example tree-based, neural network, ensemble"},
            "task": {"type": "string", "description": "ML task"},
            "audience": {"type": "string", "description": "Target audience, for example regulators, end users, researchers"},
        },
        ["query"],
    ),
    "time_series_strategy": _schema(
        "Recommend time series analysis and forecasting strategy.",
        {
            "query": _query_prop("Time series request"),
            "problem": {"type": "string", "description": "Specific problem, for example demand forecasting, anomaly detection"},
            "horizon": {"type": "string", "description": "Forecast horizon, for example short, medium, long"},
            "data_frequency": {"type": "string", "description": "Data frequency, for example minute, hourly, daily, monthly"},
        },
        ["query"],
    ),
    "solution_recommendation": _schema(
        "Recommend practical ML solution approaches and an implementation roadmap.",
        {
            "query": _query_prop("Solution recommendation request"),
            "problem": {"type": "string", "description": "Specific problem statement"},
            "constraints": {"type": "object", "description": "Optional constraints such as compute, latency, data availability"},
        },
        ["query"],
    ),
    "prototype_guidance": _schema(
        "Provide prototype development guidance for an ML use case.",
        {
            "query": _query_prop("Prototype guidance request"),
            "problem": {"type": "string", "description": "Specific use case"},
            "stack": {"type": "string", "description": "Preferred stack, for example scikit-learn, PyTorch, XGBoost"},
        },
        ["query"],
    ),
    "experiment_planner": _schema(
        "Design an experiment plan for an ML research problem.",
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


def build_mcp_server(agent_name: str = "Experiment Agent") -> FastMCP:
    return create_mcp_server(agent_name, TOOLS, TOOL_SCHEMAS)
