"""
client_gpt.py
=============

GPT client wrapper for Manion CAS-Compiler.

Policy
------
- Default: TEXT-ONLY → use gpt-4o-mini (cheaper, deterministic).
- If router says need_image=True AND image_path is present:
    → send a MULTIMODAL message (image + text) using gpt-4o.

Features
--------
- response_format={"type": "json_object"}  → model must return strict JSON
- temperature=0.0                          → deterministic outputs
- OPENAI_API_KEY from environment (optionally OPENAI_BASE_URL)
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from . import load_system_prompt


def _build_messages_text(system_prompt: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Text-only messages (for gpt-4o-mini)."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def _build_messages_multimodal(system_prompt: str, payload: Dict[str, Any], image_url: str) -> List[Dict[str, Any]]:
    """Multimodal messages (image + text) for gpt-4o."""
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False)},
            ],
        },
    ]


def call_manion_model(
    segments_json: List[Dict[str, Any]],
    problem_meta: Dict[str, Any],
    *,
    need_image: bool,
    model_text: str = "gpt-4o-mini",
    model_vision: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 4096,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Invoke GPT according to routing decision.

    Parameters
    ----------
    segments_json : list[dict]
    problem_meta  : dict  (should include router_hint; may include image_path)
    need_image    : bool  (router's decision)
    model_text    : default "gpt-4o-mini"
    model_vision  : default "gpt-4o"
    temperature   : default 0.0 (deterministic)
    base_url      : optional custom endpoint

    Returns
    -------
    dict : strict JSON produced by the model
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key, base_url=base_url or os.environ.get("OPENAI_BASE_URL"))
    system_prompt = load_system_prompt()

    # Payload passed to the model (kept stable for determinism)
    payload = {
        "segments_json": segments_json,
        "problem_meta": problem_meta,
    }

    # Choose composition & model
    if need_image and problem_meta.get("image_path"):
        messages = _build_messages_multimodal(system_prompt, payload, problem_meta["image_path"])
        model = model_vision
    else:
        messages = _build_messages_text(system_prompt, payload)
        model = model_text

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=messages,
        max_tokens=max_tokens,
    )

    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Save raw text for debugging
        os.makedirs("output_results", exist_ok=True)
        with open("output_results/last_raw_response.txt", "w", encoding="utf-8") as f:
            f.write(content or "")
        raise RuntimeError(
            f"Model did not return valid JSON: {e}. "
            f"Raw response saved to output_results/last_raw_response.txt"
        )




