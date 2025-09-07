import re
import time
import base64
import json
import logging
import os
from tomllib import load
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from openai import APIError, RateLimitError
from libs.tokens import get_openai_client
from libs.schemas import ProblemDoc, CodegenJob
from libs.layout import reading_order
from apps.router.router import PICTURE_CATS
from apps.render.fill import collect_geo_placeholders, extract_geo_labels

# -------------------------------
# Debug helpers
# -------------------------------

def _is_debug() -> bool:
    # .env 또는 프로세스 env로 활성화
    return os.getenv("MANION_DEBUG", "").lower() in {"1", "true", "yes"}

def _debug_dir(problem_name: str) -> Path:
    d = Path("ManimcodeOutput/_debug") / problem_name
    d.mkdir(parents=True, exist_ok=True)
    return d

# -------------------------------
# Config & Constants
# -------------------------------

CONFIGS = Path(__file__).parents[2] / "configs"

# SoT: 항상 system_prompt.txt만 사용
SYSTEM_PROMPT_PATH = Path(__file__).parents[2] / "system_prompt.txt"
SYSTEM_PROMPT_TEXT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

IMAGE_CATS = {"Formula", "Picture", "Diagram", "Graph", "Figure"}

def _cfg():
    with open(CONFIGS / "openai.toml", "rb") as f:
        return load(f)

def _sys_text(with_image: bool) -> str:
    # 프롬프트 선택 분기 제거
    return SYSTEM_PROMPT_TEXT

# -------------------------------
# 메시지 구성 (Responses / Chat)
# -------------------------------

def _build_user_parts_for_chat(doc: ProblemDoc, with_image: bool, has_diagram: bool) -> List[Dict[str, Any]]:
    ocr_dump = [{"bbox": i.bbox, "category": i.category, "text": i.text} for i in doc.items]
    hint = f"\n\nGEOMETRY_HINT:\n{json.dumps(getattr(doc, 'geometry_hint', None), ensure_ascii=False)}" \
        if getattr(doc, "geometry_hint", None) else ""
    meta_line = f"HAS_DIAGRAM: {str(has_diagram).lower()}"
    text = f"{meta_line}\nIMAGE_PATH: {doc.image_path or 'N/A'}\n\nOCR_JSON:\n{json.dumps(ocr_dump, ensure_ascii=False)}{hint}"

    parts: List[Dict[str, Any]] = [{"type": "text", "text": text}]
    if doc.image_path:
        try:
            img_bytes = Path(doc.image_path).read_bytes()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            parts.insert(0, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        except OSError:
            pass
    return parts

def _build_messages_for_chat(doc: ProblemDoc, with_image: bool, has_diagram: bool) -> List[Dict[str, Any]]:
    return [
        {"role": "system", "content": _sys_text(with_image)},
        {"role": "user", "content": _build_user_parts_for_chat(doc, with_image, has_diagram)},
    ]

def _build_messages_for_responses(doc: ProblemDoc, with_image: bool, has_diagram: bool) -> List[Dict[str, Any]]:
    ocr_dump = [{"bbox": i.bbox, "category": i.category, "text": i.text} for i in doc.items]
    hint = f"\n\nGEOMETRY_HINT:\n{json.dumps(getattr(doc, 'geometry_hint', None), ensure_ascii=False)}" \
        if getattr(doc, "geometry_hint", None) else ""
    meta_line = f"HAS_DIAGRAM: {str(has_diagram).lower()}"
    user_text = f"{meta_line}\nIMAGE_PATH: {doc.image_path or 'N/A'}\n\nOCR_JSON:\n{json.dumps(ocr_dump, ensure_ascii=False)}{hint}"

    user_parts: List[Dict[str, Any]] = []
    if doc.image_path:
        try:
            img_bytes = Path(doc.image_path).read_bytes()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            user_parts.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{img_b64}"})
        except OSError:
            pass
    user_parts.append({"type": "input_text", "text": user_text})

    return [
        {"role": "system", "content": [{"type": "input_text", "text": _sys_text(with_image)}]},
        {"role": "user", "content": user_parts},
    ]

# -------------------------------
# OpenAI 호출 (재시도 포함)
# -------------------------------

def _responses_create_with_retry(
    client,
    *,
    model: str,
    messages: List[Dict[str, Any]],
    max_tokens: int,
    temperature: Optional[float] = None,
):
    for i in range(3):
        try:
            kwargs = {
                "model": model,
                "input": messages,
                "response_format": {"type": "text"},
                "max_output_tokens": max_tokens,
            }
            if temperature is not None:
                kwargs["temperature"] = temperature
            return client.responses.create(**kwargs)
        except TypeError:
            try:
                kwargs = {
                    "model": model,
                    "input": messages,
                    "text": {"format": {"type": "text"}},
                }
                if temperature is not None:
                    kwargs["temperature"] = temperature
                return client.responses.create(**kwargs)
            except (RateLimitError, APIError):
                if i == 2:
                    raise
                time.sleep(2 ** i)
        except (RateLimitError, APIError):
            if i == 2:
                raise
            time.sleep(2 ** i)

def _chat_completion_with_retry(client, **kwargs):
    for i in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except (RateLimitError, APIError):
            if i == 2:
                raise
            time.sleep(2 ** i)

def _extract_text_from_responses(resp) -> str:
    text = getattr(resp, "output_text", None)
    if text:
        return text.strip()

    output = getattr(resp, "output", None)
    buf: List[str] = []
    if output:
        for item in output:
            itype = getattr(item, "type", None) or (isinstance(item, dict) and item.get("type"))
            if itype and itype != "message":
                continue
            content = getattr(item, "content", None) or (isinstance(item, dict) and item.get("content")) or []
            for part in content:
                ptype = getattr(part, "type", None) or (isinstance(part, dict) and part.get("type"))
                if ptype in {"output_text", "text"}:
                    t = getattr(part, "text", None) or (isinstance(part, dict) and part.get("text"))
                    if t:
                        buf.append(t)
    if buf:
        return "\n".join(buf).strip()

    # fallback
    data: Dict[str, Any] = {}
    try:
        data = resp.model_dump()  # type: ignore[attr-defined]
    except Exception:
        pass
    choices = data.get("choices") if isinstance(data, dict) else None
    if choices:
        content = choices[0].get("message", {}).get("content")
        if isinstance(content, str):
            return content.strip()
    error = data.get("error") if isinstance(data, dict) else None
    if error:
        logging.error("Responses API error: %s", error)

    logging.warning("Unhandled Responses output: %s", json.dumps(data, ensure_ascii=False))
    raise ValueError("No textual content found in Responses API output")

# -------------------------------
# 본체
# -------------------------------

def generate_manim(doc: ProblemDoc) -> CodegenJob:
    cfg = _cfg()
    client = get_openai_client()

    # 읽기 순서 정렬 및 geometry_hint 인계
    sorted_items = reading_order(list(doc.items))
    doc = ProblemDoc(items=sorted_items, image_path=doc.image_path, geometry_hint=getattr(doc, "geometry_hint", None))
    with_image = bool(doc.image_path) or any(i.category in IMAGE_CATS for i in doc.items)
    has_diagram = any(i.category in PICTURE_CATS for i in doc.items)

    model = cfg["models"]["codegen"]
    gen_cfg = cfg.get("gen", {})
    temperature = gen_cfg.get("temperature")
    max_tokens = gen_cfg.get("max_tokens", 4096)

    # 문제 이름(디버그 저장용)
    problem_name = Path(doc.image_path).stem if doc.image_path else "unknown"
    dd = _debug_dir(problem_name) if _is_debug() else None

    # --- LLM 호출
    if "gpt-5" in model.lower():
        # Responses API
        messages = _build_messages_for_responses(doc, with_image, has_diagram)
        resp = _responses_create_with_retry(
            client,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = _extract_text_from_responses(resp)
    else:
        # Chat Completions
        messages = _build_messages_for_chat(doc, with_image, has_diagram)
        kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens}
        if temperature is not None:
            kwargs["temperature"] = temperature
        resp = _chat_completion_with_retry(client, **kwargs)
        text = resp.choices[0].message.content.strip()

    if _is_debug() and dd:
        (dd / "01_llm_raw.txt").write_text(text, encoding="utf-8")

    # --- 파싱 (계약: <MANIM_CODE> [---GEO-JOBS---] [---CAS-JOBS---])
    manim_part = text
    geo_json_s = ""
    cas_block = ""

    if "---GEO-JOBS---" in text:
        manim_part, rest = text.split("---GEO-JOBS---", 1)
        if "---CAS-JOBS---" in rest:
            geo_json_s, cas_block = rest.split("---CAS-JOBS---", 1)
        else:
            geo_json_s = rest
    elif "---CAS-JOBS---" in text:
        manim_part, cas_block = text.split("---CAS-JOBS---", 1)
    if "---GEO-JOBS---" not in text:
        logging.warning("GEO-JOBS section missing")
    if "---CAS-JOBS---" not in text:
        logging.warning("CAS-JOBS section missing")

    # 코드펜스 제거
    manim_code = manim_part.strip()
    if manim_code.startswith("```python"):
        manim_code = manim_code[9:]
    elif manim_code.startswith("```"):
        manim_code = manim_code[3:]
    lines = manim_code.splitlines()
    if lines and lines[-1].strip() in {"```", "'''"}:
        lines = lines[:-1]
    manim_code = "\n".join(lines).strip()

    if _is_debug() and dd:
        (dd / "02_manim_code_draft.py").write_text(manim_code, encoding="utf-8")
        if geo_json_s.strip():
            (dd / "03_geo_jobs.json").write_text(geo_json_s.strip(), encoding="utf-8")
        if cas_block.strip():
            (dd / "04_cas_jobs.txt").write_text(cas_block.strip(), encoding="utf-8")

    # ConstraintSpec
    constraint_spec: Optional[Dict[str, Any]] = None
    try:
        if geo_json_s.strip():
            constraint_spec = json.loads(geo_json_s.strip())
    except Exception:
        constraint_spec = None  # GeoCAS가 힌트/기본값으로 시도

    # CAS jobs
    jobs: List[Dict[str, Any]] = []
    for line in cas_block.strip().splitlines():
        m = re.match(r"\[\[CAS:(?P<id>[A-Za-z0-9_]+):(?P<expr>.+)\]\]$", line.strip())
        if m:
            jobs.append({"id": m["id"], "expr": m["expr"]})

    # 코드 내 [[CAS:id:expr]] → [[CAS:id]] 표면 정리
    def _strip_expr(match):
        return f"[[CAS:{match.group('id')}]]"
    draft = re.sub(r"\[\[CAS:(?P<id>[A-Za-z0-9_]+):(?P<expr>.*?)\]\]", _strip_expr, manim_code)

    # -------------------------------
    # HARD GUARD (codegen-level)
    # -------------------------------
    geo_keys: Set[str] = collect_geo_placeholders(draft)
    if has_diagram and not geo_keys:
        raise ValueError("Diagram detected but no GEO placeholders in MANIM_CODE.")
    if has_diagram and constraint_spec is None:
        raise ValueError("GEO placeholders present but ---GEO-JOBS--- (ConstraintSpec) is missing.")
    if has_diagram and constraint_spec is not None:
        used_labels: Set[str] = extract_geo_labels(geo_keys)  # {"A","B","C",...}
        try:
            points_list = constraint_spec.get("entities", {}).get("points", [])
            declared: Set[str] = {str(x) for x in points_list}
        except Exception:
            declared = set()
        missing = sorted(list(used_labels - declared))
        if missing:
            raise ValueError(
                f"GEO labels missing in ConstraintSpec.entities.points: {missing}. "
                "All labels referenced in [[GEO:*]] must be declared."
            )

    # 최종 결과 반환
    return CodegenJob(
        manim_code_draft=draft,
        cas_jobs=jobs,
        constraint_spec=constraint_spec
    )
