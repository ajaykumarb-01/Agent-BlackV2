import re
import json
import asyncio

from shared.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL,
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL,
)


def extract_json(raw: str) -> dict:
    """
    Robustly extract JSON from an LLM response that may contain:
    - Markdown fences (```json ... ``` or ``` ... ```)
    - Leading/trailing whitespace or newlines
    - Text before or after the JSON block
    """
    if not raw or not raw.strip():
        raise ValueError("Empty LLM response")

    text = raw.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON object or array in the text
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:200]}")


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai
    client_opts = {"api_key": GEMINI_API_KEY}
    if GEMINI_BASE_URL:
        client_opts["client_options"] = {"api_endpoint": GEMINI_BASE_URL}
    genai.configure(**client_opts)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    response = genai.GenerativeModel(GEMINI_MODEL).generate_content(full_prompt)
    return response.text


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def _call_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic
    client_kwargs = {"api_key": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        client_kwargs["base_url"] = ANTHROPIC_BASE_URL
    client = anthropic.Anthropic(**client_kwargs)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def call_llm(system_prompt: str, user_prompt: str) -> str:
    if LLM_PROVIDER == "gemini":
        return _call_gemini(system_prompt, user_prompt)
    if LLM_PROVIDER == "openai":
        return _call_openai(system_prompt, user_prompt)
    if LLM_PROVIDER == "anthropic":
        return _call_anthropic(system_prompt, user_prompt)
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Choose from: gemini, openai, anthropic")


async def async_call_llm(system_prompt: str, user_prompt: str) -> str:
    """Async wrapper around call_llm that runs in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(call_llm, system_prompt, user_prompt)
