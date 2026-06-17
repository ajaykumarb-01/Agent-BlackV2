import re
import json
import asyncio
import time
import logging

import anthropic

from shared.config import get_setting

logger = logging.getLogger(__name__)

LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2


def _get_llm_config() -> dict:
    """Read LLM config from SQLite at call time (not import time)."""
    provider = get_setting("LLM_PROVIDER", "gemini")
    return {
        "provider": provider,
        "gemini_api_key": get_setting("GEMINI_API_KEY"),
        "gemini_base_url": get_setting("GEMINI_BASE_URL"),
        "gemini_model": get_setting("GEMINI_MODEL", "gemini-1.5-flash"),
        "openai_api_key": get_setting("OPENAI_API_KEY"),
        "openai_base_url": get_setting("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "openai_model": get_setting("OPENAI_MODEL", "gpt-4o"),
        "anthropic_api_key": get_setting("ANTHROPIC_API_KEY"),
        "anthropic_base_url": get_setting("ANTHROPIC_BASE_URL"),
        "anthropic_model": get_setting("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    }


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


def _call_gemini(system_prompt: str, user_prompt: str, cfg: dict, json_mode: bool = False) -> str:
    import google.generativeai as genai
    client_opts = {"api_key": cfg["gemini_api_key"]}
    if cfg["gemini_base_url"]:
        client_opts["client_options"] = {"api_endpoint": cfg["gemini_base_url"]}
    genai.configure(**client_opts)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    if json_mode:
        full_prompt += "\n\nReturn ONLY a single valid JSON object. No prose, no markdown fences."
    response = genai.GenerativeModel(cfg["gemini_model"]).generate_content(full_prompt)
    return response.text


def _call_openai(system_prompt: str, user_prompt: str, cfg: dict, json_mode: bool = False) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=cfg["openai_api_key"], base_url=cfg["openai_base_url"])
    kwargs: dict = {
        "model": cfg["openai_model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def _call_anthropic(system_prompt: str, user_prompt: str, cfg: dict, json_mode: bool = False) -> str:
    from anthropic import Anthropic
    client_kwargs = {"api_key": cfg["anthropic_api_key"]}
    if cfg["anthropic_base_url"]:
        client_kwargs["base_url"] = cfg["anthropic_base_url"]
    client = anthropic.Anthropic(**client_kwargs)
    user_content = user_prompt
    if json_mode:
        user_content += "\n\nReturn ONLY a single valid JSON object. No prose, no markdown fences."
    response = client.messages.create(
        model=cfg["anthropic_model"],
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


def _call_llm_once(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    cfg = _get_llm_config()
    provider = cfg["provider"]
    if provider == "gemini":
        return _call_gemini(system_prompt, user_prompt, cfg, json_mode=json_mode)
    if provider == "openai":
        return _call_openai(system_prompt, user_prompt, cfg, json_mode=json_mode)
    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, cfg, json_mode=json_mode)
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Choose from: gemini, openai, anthropic")


def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    last_error = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            return _call_llm_once(system_prompt, user_prompt, json_mode=json_mode)
        except Exception as e:
            last_error = e
            logger.warning(f"LLM call attempt {attempt + 1}/{LLM_MAX_RETRIES} failed: {e}")
            if attempt < LLM_MAX_RETRIES - 1:
                time.sleep(LLM_RETRY_DELAY * (attempt + 1))
    raise RuntimeError(f"LLM call failed after {LLM_MAX_RETRIES} attempts: {last_error}")


async def async_call_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Async wrapper around call_llm that runs in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(call_llm, system_prompt, user_prompt, json_mode=json_mode)
