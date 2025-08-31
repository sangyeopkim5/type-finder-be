import re
import time
import base64
from tomllib import load
from pathlib import Path
from typing import List, Dict, Any
from openai import APIError, RateLimitError
from libs.tokens import get_openai_client
from libs.schemas import ProblemDoc, CodegenJob
from libs.layout import reading_order


TEMPLATES = Path(__file__).parent / "prompt_templates"
CONFIGS = Path(__file__).parents[2] / "configs"


def _cfg():
    with open(CONFIGS / "openai.toml", "rb") as f:
        return load(f)


def _sys_text(with_image: bool) -> str:
    base = (TEMPLATES / ("base_vision.md" if with_image else "base_text.md")).read_text(
        encoding="utf-8"
    )
    return base


def _build_messages(doc: ProblemDoc, with_image: bool) -> List[Dict[str, Any]]:
    ocr_dump = [{"bbox": i.bbox, "category": i.category, "text": i.text} for i in doc.items]
    user_parts: List[Dict[str, Any]] = []
    if doc.image_path:
        try:
            img_bytes = Path(doc.image_path).read_bytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            # OpenAI API는 "type": "image_url"을 사용하며, data URL 스키마로 base64 전달
            user_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
        except OSError:
            pass
    user_text = "IMAGE_PATH: " + (doc.image_path or "N/A") + "\n\nOCR_JSON:\n" + str(ocr_dump)
    user_parts.append({"type": "text", "text": user_text})
    return [
        {"role": "system", "content": _sys_text(with_image)},
        {"role": "user", "content": user_parts},
    ]


def _chat_completion_with_retry(client, **kwargs):
    for i in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except (RateLimitError, APIError):
            if i == 2:
                raise
            time.sleep(2 ** i)


IMAGE_CATS = {"Formula", "Picture", "Diagram", "Graph", "Figure"}


def generate_manim(doc: ProblemDoc) -> CodegenJob:
    cfg = _cfg()
    client = get_openai_client()
    sorted_items = reading_order(list(doc.items))
    doc = ProblemDoc(items=sorted_items, image_path=doc.image_path)
    with_image = bool(doc.image_path) or any(i.category in IMAGE_CATS for i in doc.items)
    messages = _build_messages(doc, with_image)

    resp = _chat_completion_with_retry(
        client,
        model=cfg["models"]["codegen"],
        messages=messages,
        temperature=cfg["gen"]["temperature"],
        max_tokens=cfg["gen"]["max_tokens"],
    )
    text = resp.choices[0].message.content.strip()

    if "---CAS-JOBS---" in text:
        manim_code, jobs_block = text.split("---CAS-JOBS---", 1)
    else:
        raise ValueError("Codegen output missing ---CAS-JOBS--- separator")
    
    # 코드 블록 마커 제거 (맨 처음과 맨 마지막만)
    manim_code = manim_code.strip()
    
    # 맨 처음 ```python 또는 ``` 제거
    if manim_code.startswith("```python"):
        manim_code = manim_code[9:]
    elif manim_code.startswith("```"):
        manim_code = manim_code[3:]
    
    # 맨 마지막 ``` 또는 ''' 제거 (중간의 마커는 보존)
    # 여러 줄로 구성된 코드에서 마지막 줄의 마커만 제거
    lines = manim_code.split('\n')
    if lines and lines[-1].strip() in ['```', "'''"]:
        lines = lines[:-1]
    manim_code = '\n'.join(lines)
    
    # 앞뒤 공백 제거
    manim_code = manim_code.strip()

    jobs = []
    for line in jobs_block.strip().splitlines():
        m = re.match(r"\[\[CAS:(?P<id>[A-Za-z0-9_]+):(?P<expr>.+)\]\]$", line.strip())
        if m:
            jobs.append({"id": m["id"], "expr": m["expr"]})
    if not jobs:
        raise ValueError("No CAS jobs parsed")

    def _strip_expr(match):
        return f"[[CAS:{match.group('id')}]]"

    draft = re.sub(r"\[\[CAS:(?P<id>[A-Za-z0-9_]+):(?P<expr>.*?)\]\]", _strip_expr, manim_code)

    return CodegenJob(manim_code_draft=draft, cas_jobs=jobs)

