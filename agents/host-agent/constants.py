"""Orchestrator constants: agent domains, keywords, and display names."""

# ── Per-agent domain keywords for routing validation ────────────────────────
# Used to filter out agents that don't match the query's domain.
# If the LLM incorrectly selects an agent from the wrong domain, this filter
# drops it. If the correct agent is offline, the query fails with
# "no_suitable_agent" instead of silently routing to the wrong agent.

AGENT_DOMAINS: dict[str, dict] = {
    "research": {
        "description": "Computer Vision",
        "keywords": [
            "vision", "image", "video", "cv", "object detection", "segmentation",
            "classification", "ocr", "face", "pose", "depth", "3d", "point cloud",
            "medical imaging", "radiology", "ct", "mri", "x-ray", "histopathology",
            "satellite", "aerial", "remote sensing", "document analysis",
            "vision-language", "vlm", "clip", "sam", "diffusion", "gan",
            "yolo", "resnet", "vit", "transformer", "cnn", "backbone",
            "paper", "arxiv", "survey", "benchmark", "dataset",
            "find papers", "search papers", "literature review",
            "find datasets", "cv datasets", "image datasets",
            "recommend models", "model recommendation", "architecture comparison",
            "research", "proposal", "proof of concept",
        ],
    },
    "solution": {
        "description": "NLP Solutions",
        "keywords": [
            "nlp", "text", "language", "llm", "gpt", "bert", "transformer",
            "rag", "retrieval", "embedding", "vector", "semantic search",
            "prompt", "prompt engineering", "fine-tuning", "fine tuning",
            "chatbot", "dialogue", "conversational", "qa", "question answering",
            "summarization", "translation", "sentiment", "ner", "named entity",
            "information extraction", "text classification", "spam detection",
            "named entity recognition", "relation extraction",
            "document", "corpus", "tokenization", "word embedding",
            "openai", "anthropic", "gemini", "claude", "llama", "mistral",
            "inference", "deployment", "serving", "pipeline",
            "design rag", "rag pipeline", "knowledge base",
            "llm benchmark", "llm evaluation", "prompt optimization",
            "information extraction", "text processing",
        ],
    },
    "experiment": {
        "description": "ML Experiment Design",
        "keywords": [
            "experiment", "training", "hyperparameter", "tuning", "optimization",
            "metric", "evaluation", "accuracy", "precision", "recall", "f1",
            "auc", "roc", "confusion matrix", "cross validation",
            "feature engineering", "feature selection", "data preprocessing",
            "model selection", "model comparison", "ablation",
            "benchmark", "leaderboard", "baseline",
            "time series", "forecasting", "regression",
            "pipeline", "workflow", "mlops", "tracking", "mlflow",
            "explainability", "interpretability", "shap", "lime",
            "hyperparameter tuning", "grid search", "random search",
            "evaluation plan", "experiment design", "experiment planning",
            "model explainability", "feature importance",
        ],
    },
}

# Friendly display names for each agent (used in error messages).
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "research": "CV Research Agent",
    "solution": "NLP Solution Agent",
    "experiment": "ML Experiment Agent",
}

# ── Research-relevance gate keywords ────────────────────────────────────────

RESEARCH_DOMAINS: list[str] = [
    "computer vision", "image classification", "object detection", "segmentation",
    "medical imaging", "video analytics", "vision-language", "nlp", "llm",
    "natural language", "rag", "retrieval augmented", "prompt engineering",
    "text classification", "summarization", "conversational ai", "information extraction",
    "machine learning", "deep learning", "neural network", "model selection",
    "feature engineering", "time series", "hyperparameter", "experiment design",
    "evaluation strategy", "research", "dataset", "benchmark", "architecture",
    "transformer", "cnn", "diffusion", "gan", "reinforcement learning",
    "paper", "arxiv", "research proposal", "proof of concept",
]

RESEARCH_ACTIONS: list[str] = [
    "recommend", "compare", "find", "search", "summarize", "analyze", "evaluate",
    "benchmark", "design", "plan", "prototype", "implement", "improve", "optimize",
    "select", "review", "survey", "study", "explore",
]

NON_RESEARCH_PATTERNS: list[str] = [
    "weather", "movie", "song", "lyrics", "joke", "meme", "recipe", "restaurant",
    "sports score", "cricket score", "football score", "stock price", "bitcoin price",
    "translate this", "write birthday", "instagram caption", "what is my ip",
    "who are you", "hello", "hi", "good morning", "good night",
]

AMBIGUOUS_HINTS: list[str] = [
    "model", "accuracy", "dataset", "classification", "training", "prediction",
    "evaluation", "architecture", "experiment",
]

NOT_RESEARCH_RESPONSE: dict = {
    "error": "not_research_query",
    "message": (
        "This query does not appear to be related to AI/ML research. "
        "This system is a Research Assistant that helps with: Computer Vision, "
        "NLP, Machine Learning research — including literature review, dataset "
        "recommendation, model selection, experiment planning, and prototype "
        "guidance. Ask a research-related question."
    ),
    "reason": "The query does not look like a research, dataset, model, experiment, or prototype request.",
    "suggestion": "Try asking about papers, datasets, models, evaluation metrics, experiment design, or prototype guidance.",
    "supported_topics": [
        "Research paper discovery and summarization",
        "Dataset recommendation (CV, NLP, ML)",
        "Model/architecture recommendation",
        "Experiment design and planning",
        "Benchmark search and comparison",
        "Research gap analysis",
        "Prototype development guidance",
    ],
}
