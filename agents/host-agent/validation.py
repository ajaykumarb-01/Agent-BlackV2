"""Query validation: research-relevance gate and domain classification."""

from shared.llm import async_call_llm, extract_json

from constants import (
    AGENT_DOMAINS,
    RESEARCH_ACTIONS,
    RESEARCH_DOMAINS,
    NON_RESEARCH_PATTERNS,
    AMBIGUOUS_HINTS,
    NOT_RESEARCH_RESPONSE,
)


def build_not_research_response(reason: str, validation: dict | None = None) -> dict:
    response = dict(NOT_RESEARCH_RESPONSE)
    response["reason"] = reason
    if validation:
        response["validation"] = validation
    return response


def rule_based_validation(query: str) -> dict:
    """Score a query against research keywords without an LLM call."""
    import re
    query_lower = query.lower().strip()
    tokens = [t for t in query_lower.replace("/", " ").replace("-", " ").split() if t]
    token_set = set(tokens)

    matched_domains = [d for d in RESEARCH_DOMAINS if d in query_lower]
    matched_actions = [a for a in RESEARCH_ACTIONS if a in query_lower]

    # Negative patterns: use word-boundary match for short patterns to avoid
    # false positives (e.g. "hi" matching inside "this" or "which").
    matched_negative = []
    for p in NON_RESEARCH_PATTERNS:
        if len(p) <= 3:
            if p in token_set:
                matched_negative.append(p)
        else:
            if p in query_lower:
                matched_negative.append(p)

    matched_ambiguous = [h for h in AMBIGUOUS_HINTS if h in query_lower]

    score = 0
    if len(query_lower) >= 12:
        score += 1
    if "?" in query or len(tokens) >= 4:
        score += 1
    score += min(len(matched_domains), 3) * 2
    score += min(len(matched_actions), 2)
    score += min(len(matched_ambiguous), 2)
    score -= min(len(matched_negative), 3) * 3

    if len(query_lower) < 5 or matched_negative:
        decision = "reject"
    elif matched_domains and (matched_actions or len(tokens) >= 4):
        decision = "accept"
    elif score >= 4:
        decision = "accept"
    elif score <= 0:
        decision = "reject"
    else:
        decision = "ambiguous"

    return {
        "decision": decision,
        "score": score,
        "matched_domains": matched_domains,
        "matched_actions": matched_actions,
        "matched_negative": matched_negative,
        "matched_ambiguous": matched_ambiguous,
    }


async def validate_research_query(query: str) -> dict:
    """Hybrid rule-based + LLM classifier for research relevance."""
    query_lower = query.lower().strip()
    if len(query_lower) < 5:
        return {
            "is_research": False,
            "method": "rule_based",
            "reason": "The query is too short to classify as a research request.",
            "rule_based": rule_based_validation(query),
        }

    rule_result = rule_based_validation(query)
    if rule_result["decision"] == "accept":
        return {
            "is_research": True,
            "method": "rule_based",
            "reason": "The query contains clear research-related keywords and intent.",
            "rule_based": rule_result,
        }
    if rule_result["decision"] == "reject":
        return {
            "is_research": False,
            "method": "rule_based",
            "reason": "The query matches non-research patterns or lacks research intent.",
            "rule_based": rule_result,
        }

    # Ambiguous — ask the LLM to classify
    gate_prompt = (
        "You are a research query classifier. Determine if the following query "
        "is related to AI, Machine Learning, Computer Vision, NLP, academic/"
        "scientific research, datasets, model selection, evaluation, experiments, "
        "or prototype guidance.\n\n"
        "Respond ONLY with valid JSON in this shape:\n"
        '{"is_research": true, "reason": "brief reason", '
        '"category": "research|implementation|general|other"}\n\n'
        f"Query: {query}"
    )
    try:
        raw = await async_call_llm(
            system_prompt=(
                "You are a strict classifier. Accept only queries that clearly ask "
                "for AI/ML/CV/NLP research help, evaluation, experiments, models, "
                "datasets, or prototype guidance."
            ),
            user_prompt=gate_prompt,
        )
        ai_result = extract_json(raw)
        return {
            "is_research": bool(ai_result.get("is_research", False)),
            "method": "hybrid_ai",
            "reason": str(ai_result.get("reason", "Classification completed.")),
            "category": ai_result.get("category", "other"),
            "rule_based": rule_result,
        }
    except Exception:
        return {
            "is_research": False,
            "method": "rule_based_fallback",
            "reason": "The query is ambiguous and the AI validator was unavailable.",
            "rule_based": rule_result,
        }


def classify_query_domains(query: str) -> set[str]:
    """Classify which agent domains match the query using keyword matching.

    Returns a set of matching domain names: 'research', 'solution', 'experiment'.
    Empty set means the query is too ambiguous to assign a domain.
    """
    query_lower = query.lower().strip()
    matches: dict[str, int] = {}
    for domain, info in AGENT_DOMAINS.items():
        score = sum(1 for kw in info["keywords"] if kw in query_lower)
        if score > 0:
            matches[domain] = score
    if not matches:
        return set()
    max_score = max(matches.values())
    threshold = max(1, max_score // 3)
    return {d for d, s in matches.items() if s >= threshold}


def filter_by_domain(
    selected: list[dict], query: str
) -> tuple[list[dict], list[str]]:
    """Drop agents that don't match the query's domain."""
    domains = classify_query_domains(query)
    if not domains:
        return selected, []

    valid: list[dict] = []
    drops: list[str] = []
    for entry in selected:
        name = entry["name"]
        if name in domains:
            valid.append(entry)
        else:
            agent_desc = AGENT_DOMAINS.get(name, {}).get("description", name)
            query_domains = ", ".join(AGENT_DOMAINS[d]["description"] for d in domains)
            drops.append(
                f"agent '{name}' ({agent_desc}) does not match query domain ({query_domains})"
            )
    return valid, drops
