from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 내부 파이프라인 구성요소 (엔드포인트는 노출하지 않음)
from apps.router.router import route_problem
from apps.codegen.codegen import generate_manim
from apps.cas.compute import run_geocas, run_cas
from apps.render.fill import (
    fill_placeholders,
    collect_geo_placeholders,
    collect_cas_placeholders,
    detect_invalid_cas_token_patterns,
    extract_geo_labels,
)
from libs.schemas import ProblemDoc, OCRItem, CASJob
from libs.layout import extract_primitives_from_image, build_geo_replacements

app = FastAPI(title="Manion-CAS (E2E-only)")

# ──────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

# ──────────────────────────────────────────────────────────
# 모델
# ──────────────────────────────────────────────────────────
class E2EInput(BaseModel):
    image_path: Optional[str] = None
    json_path: str

class E2EOutput(BaseModel):
    manim_code: str

# ──────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────
def _load_problem_from_paths(image_path: Optional[str], json_path: str) -> ProblemDoc:
    p = Path(json_path)
    try:
        items_raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"OCR JSON load failed: {e}")
    items = [OCRItem(**it) for it in items_raw]
    return ProblemDoc(items=items, image_path=str(image_path) if image_path else None)

def _run_e2e(doc: ProblemDoc) -> str:
    # 1) 라우팅(정규화)
    meta = route_problem(doc)

    # 2) GeometryHint (이미지 + OCR 라벨 기반)
    ocr_dump = [{"bbox": i.bbox, "category": i.category, "text": i.text} for i in doc.items]
    geometry_hint = extract_primitives_from_image(doc.image_path, ocr_json=ocr_dump)
    doc.geometry_hint = geometry_hint

    # 3) Codegen (하드가드 포함)
    cj = generate_manim(doc)

    # 3.1) 사전 검증 (fail fast)
    geo_needed: Set[str] = collect_geo_placeholders(cj.manim_code_draft)

    if meta.get("has_diagram") and not geo_needed:
        raise HTTPException(status_code=422, detail="Diagram detected but no GEO placeholders.")
    if geo_needed and not getattr(cj, "constraint_spec", None):
        raise HTTPException(status_code=422, detail="GEO placeholders present but ---GEO-JOBS--- (ConstraintSpec) is missing.")

    if getattr(cj, "constraint_spec", None):
        needed_labels = extract_geo_labels(geo_needed)
        entities = (cj.constraint_spec or {}).get("entities", {})
        declared = set((entities.get("points", []) or []))
        missing = sorted(list(needed_labels - declared))
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"ConstraintSpec.entities.points missing labels used in GEO tokens: {missing}"
            )

    offenders = detect_invalid_cas_token_patterns(cj.manim_code_draft)
    if offenders:
        raise HTTPException(status_code=422, detail=f"Malformed CAS token(s): {offenders[:3]}")

    cas_needed: Set[str] = collect_cas_placeholders(cj.manim_code_draft)
    job_ids = {j.get("id") for j in (cj.cas_jobs or [])}
    if cas_needed and not job_ids:
        raise HTTPException(status_code=422, detail="CAS placeholders present but ---CAS-JOBS--- is missing.")
    missing_cas = sorted(list(cas_needed - job_ids))
    if missing_cas:
        raise HTTPException(status_code=422, detail=f"CAS placeholders without matching jobs: {missing_cas}")

    # 4) GeoCAS
    exact = {}
    if getattr(cj, "constraint_spec", None):
        exact = run_geocas(constraint_spec=cj.constraint_spec, geometry_hint=geometry_hint)
        # 선언된 포인트가 모두 풀렸는지 체크(선택)
        declared = set((cj.constraint_spec.get("entities", {}) or {}).get("points", []) or [])
        solved = set((exact.get("points", {}) or {}).keys())
        unsolved = sorted(list(declared - solved))
        if unsolved:
            raise HTTPException(status_code=422, detail=f"GeoCAS could not solve coordinates for: {unsolved}")

    geo_repls = build_geo_replacements(exact=exact, hint=geometry_hint, decimals=6)

    # 5) CAS
    cas_repls: List[Dict[str, Any]] = []
    if cj.cas_jobs:
        jobs = [CASJob(**j) for j in cj.cas_jobs]
        cas_repls = run_cas(jobs)

    # 6) 치환 (on_missing=fail_build)
    filled = fill_placeholders(
        draft=cj.manim_code_draft,
        repls=cas_repls,
        geo_replacements=geo_repls,
        on_missing="fail_build",
    )
    return filled.manim_code_final

# ──────────────────────────────────────────────────────────
# E2E 엔드포인트 (유일 권장 경로)
# ──────────────────────────────────────────────────────────
@app.post("/e2e", response_model=E2EOutput)
def e2e(input: E2EInput) -> E2EOutput:
    doc = _load_problem_from_paths(input.image_path, input.json_path)
    code = _run_e2e(doc)
    # 저장(옵션)
    out_root = Path("ManimcodeOutput"); out_root.mkdir(exist_ok=True)
    problem_name = Path(input.image_path).stem if input.image_path else "unknown"
    problem_dir = out_root / problem_name; problem_dir.mkdir(exist_ok=True)
    (problem_dir / f"{problem_name}.py").write_text(code, encoding="utf-8")
    (problem_dir / "README.md").write_text(
        f"# {problem_name} Manim Code\n\n```bash\nmanim {problem_name}.py -pql\n```",
        encoding="utf-8"
    )
    return E2EOutput(manim_code=code)
