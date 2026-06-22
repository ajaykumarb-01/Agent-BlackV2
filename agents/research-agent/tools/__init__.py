from .paper_search import search_papers
from .summarizer import summarize_paper
from .gap_analysis import analyze_gaps
from .cv_datasets import find_cv_datasets
from .cv_models import recommend_cv_models
from .citation_generator import citation_generator
from .benchmark_search import benchmark_search_cv
from .eval_advisor import eval_metric_advisor_cv
from .architecture_comparison import architecture_comparison
from .synthetic_data import synthetic_data_strategy
from .solution_recommendation import solution_recommendation
from .prototype_guidance import prototype_guidance
from .experiment_planner import experiment_planner

TOOLS = {
    "search_papers": search_papers,
    "summarize_paper": summarize_paper,
    "analyze_gaps": analyze_gaps,
    "find_cv_datasets": find_cv_datasets,
    "recommend_cv_models": recommend_cv_models,
    "citation_generator": citation_generator,
    "benchmark_search": benchmark_search_cv,
    "eval_metric_advisor": eval_metric_advisor_cv,
    "architecture_comparison": architecture_comparison,
    "synthetic_data_strategy": synthetic_data_strategy,
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
            "domain": {"type": "string", "description": "Optional CV domain filter, for example medical imaging or object detection"},
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
        "Analyze research gaps from a query and optional paper context.",
        {
            "query": _query_prop(),
            "papers": {"type": "array", "items": {"type": "object"}, "description": "Optional paper records from search_papers"},
            "focus": {"type": "string", "description": "Optional gap-analysis focus, for example methodology, datasets, metrics"},
        },
        ["query"],
    ),
    "find_cv_datasets": _schema(
        "Find real computer vision datasets from Hugging Face Datasets, Kaggle, and Papers With Code.",
        {
            "query": _query_prop("Dataset topic or keyword"),
            "topic": {"type": "string", "description": "Dataset topic, for example retinal OCT segmentation"},
            "domain": {"type": "string", "description": "CV domain, for example medical imaging, remote sensing, video"},
            "task": {"type": "string", "description": "Dataset task, for example object detection, semantic segmentation"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "sources": {"type": "array", "items": {"type": "string", "enum": ["huggingface", "kaggle", "paperswithcode"]}, "default": ["huggingface", "kaggle", "paperswithcode"]},
        },
        ["query"],
    ),
    "recommend_cv_models": _schema(
        "Recommend computer vision model architectures for a task with constraints.",
        {
            "query": _query_prop("Model architecture recommendation request"),
            "problem": {"type": "string", "description": "Specific CV problem statement"},
            "domain": {"type": "string", "description": "CV domain"},
            "task": {"type": "string", "description": "CV task"},
            "constraints": {"type": "object", "description": "Optional constraints such as latency, GPU memory, accuracy, deployment target"},
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
    "benchmark_search": _schema(
        "Search real Papers With Code benchmark/task data without hallucinating SOTA scores.",
        {
            "query": _query_prop("Benchmark task or dataset query"),
            "task": {"type": "string", "description": "Specific benchmark task, for example semantic segmentation on Cityscapes"},
            "domain": {"type": "string", "description": "CV domain"},
            "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            "sources": {"type": "array", "items": {"type": "string", "enum": ["paperswithcode"]}, "default": ["paperswithcode"]},
        },
        ["query"],
    ),
    "eval_metric_advisor": _schema(
        "Recommend evaluation metrics for a CV task.",
        {
            "query": _query_prop("Evaluation metric request"),
            "task": {"type": "string", "description": "CV task"},
            "domain": {"type": "string", "description": "CV domain"},
            "modality": {"type": "string", "description": "Image, video, 3D, medical, remote sensing, etc."},
        },
        ["query"],
    ),
    "architecture_comparison": _schema(
        "Compare CV architectures for a task and optional constraints.",
        {
            "query": _query_prop("Architecture comparison request"),
            "task": {"type": "string", "description": "CV task"},
            "architectures": {"type": "array", "items": {"type": "string"}, "description": "Architectures to compare"},
            "constraints": {"type": "object", "description": "Optional constraints such as speed, parameters, memory, deployment"},
        },
        ["query"],
    ),
    "synthetic_data_strategy": _schema(
        "Recommend synthetic data and augmentation strategies for a CV domain.",
        {
            "query": _query_prop("Synthetic data request"),
            "domain": {"type": "string", "description": "CV domain"},
            "task": {"type": "string", "description": "CV task"},
            "data_constraints": {"type": "array", "items": {"type": "string"}, "description": "Data limitations or privacy constraints"},
        },
        ["query"],
    ),
    "solution_recommendation": _schema(
        "Recommend practical computer vision solution approaches and an implementation roadmap.",
        {
            "query": _query_prop("Solution recommendation request"),
            "problem": {"type": "string", "description": "Specific problem statement"},
            "constraints": {"type": "object", "description": "Optional constraints such as compute, latency, data availability"},
        },
        ["query"],
    ),
    "prototype_guidance": _schema(
        "Provide prototype development guidance for a CV use case.",
        {
            "query": _query_prop("Prototype guidance request"),
            "problem": {"type": "string", "description": "Specific use case"},
            "stack": {"type": "string", "description": "Preferred stack, for example PyTorch, TensorFlow, ONNX"},
        },
        ["query"],
    ),
    "experiment_planner": _schema(
        "Design an experiment plan for a CV research problem.",
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


def build_mcp_server(agent_name: str = "Research Agent") -> FastMCP:
    return create_mcp_server(agent_name, TOOLS, TOOL_SCHEMAS)
