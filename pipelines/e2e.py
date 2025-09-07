from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, Any

from pydantic import BaseModel

from libs.schemas import ProblemDoc, OCRItem, CASJob
from libs.layout import extract_primitives_from_image, build_geo_replacements
from apps.router.router import route_problem
from apps.codegen.codegen import generate_manim
from apps.cas.compute import run_cas, run_geocas
from apps.render.fill import (
    fill_placeholders,
    collect_geo_placeholders,
    collect_cas_placeholders,
    detect_invalid_cas_token_patterns,
    extract_geo_labels,
)

# -------------------------------
# Debug helpers
# -------------------------------

def _is_debug() -> bool:
    return os.getenv("MANION_DEBUG", "").lower() in {"1", "true", "yes"}

def _dbgdir(image_path: str | None) -> Path:
    prob = Path(image_path).stem if image_path else "unknown"
    d = Path("ManimcodeOutput/_debug") / prob
    d.mkdir(parents=True, exist_ok=True)
    return d

def _dump_json(path: Path, data: Any) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # best-effort only
        pass

# -------------------------------
# Pipeline
# -------------------------------

def load_problem(image_path: str, ocr_json_path: str) -> ProblemDoc:
    image_p = Path(image_path)
    ocr_p = Path(ocr_json_path)
    items_raw = json.loads(ocr_p.read_text(encoding="utf-8"))
    items = [OCRItem(**it) for it in items_raw]
    return ProblemDoc(items=items, image_path=str(image_p))

def run_pipeline(doc: ProblemDoc) -> str:
    dd = _dbgdir(doc.image_path) if _is_debug() else None

    # 1) 라우팅(정규화)
    meta: Dict[str, Any] = route_problem(doc)
    if _is_debug() and dd:
        _dump_json(dd / "99_meta.route.json", meta)

    # 2) GeometryHint (이미지 + OCR 라벨 기반)
    ocr_dump = [{"bbox": i.bbox, "category": i.category, "text": i.text} for i in doc.items]
    geometry_hint = extract_primitives_from_image(doc.image_path, ocr_json=ocr_dump)
    doc.geometry_hint = geometry_hint
    if _is_debug() and dd:
        _dump_json(dd / "10_geometry_hint.json", geometry_hint)

    # 3) Codegen (GEO/CAS 작업 분리된 초안; codegen 내부 하드가드 포함)
    cg = generate_manim(doc)

    print("----- GEO TOKENS (raw) -----")
    print(cg.manim_code_draft)
    print("----- /GEO TOKENS (raw) -----")

    # 디버그 저장 (codegen이 01~04를 남기지만, 여기서도 초안 백업)
    if _is_debug() and dd:
        (dd / "02_manim_code_draft.py").write_text(cg.manim_code_draft, encoding="utf-8")
        if getattr(cg, "constraint_spec", None) is not None:
            _dump_json(dd / "11_constraint_spec.json", getattr(cg, "constraint_spec"))
        if getattr(cg, "cas_jobs", None):
            (dd / "04_cas_jobs.txt").write_text(
                "\n".join([f"[[CAS:{j.get('id')}:{j.get('expr')}]]" for j in cg.cas_jobs]),
                encoding="utf-8",
            )

    # ConstraintSpec는 Pydantic 모델일 수 있으므로 dict로 변환
    raw_cs = getattr(cg, "constraint_spec", None)
    if isinstance(raw_cs, BaseModel):
        constraint_spec = raw_cs.model_dump()
    else:
        constraint_spec = raw_cs or {}

    # 3.1) Pre-validate placeholders vs job sections (fail fast)
    geo_needed = collect_geo_placeholders(cg.manim_code_draft)

    if meta.get("has_diagram") and not geo_needed:
        raise ValueError("Diagram detected but no GEO placeholders.")
    if (not meta.get("has_diagram")) and (geo_needed or constraint_spec):
        raise ValueError("GEO artifacts present without diagram.")
    if geo_needed and not constraint_spec:
        raise ValueError("GEO placeholders present but ---GEO-JOBS--- (ConstraintSpec) is missing.")

    # GEO 라벨 선언 일치
    if constraint_spec:
        needed_labels = extract_geo_labels(geo_needed)
        entities = constraint_spec.get("entities", {}) if constraint_spec else {}
        declared = set((entities.get("points", []) or []))
        missing_labels = sorted(list(needed_labels - declared))
        if missing_labels:
            raise ValueError(
                "ConstraintSpec.entities.points missing labels used in GEO tokens: "
                f"{missing_labels}"
            )

    offenders = detect_invalid_cas_token_patterns(cg.manim_code_draft)
    if offenders:
        raise ValueError(f"Dynamic/malformed CAS token detected. Use literal [[CAS:ID]]. Offenders: {offenders[:3]}")

    cas_needed = collect_cas_placeholders(cg.manim_code_draft)
    job_ids = {j.get("id") for j in (cg.cas_jobs or [])}
    if cas_needed and not job_ids:
        raise ValueError("CAS placeholders present but ---CAS-JOBS--- is missing.")
    missing_cas = sorted(list(cas_needed - job_ids))
    if missing_cas:
        raise ValueError(f"CAS placeholders without matching jobs: {missing_cas}")

    # 4) GeoCAS (기하 해 계산)
    exact = run_geocas(constraint_spec=constraint_spec, hint=geometry_hint)
    if _is_debug() and dd:
        _dump_json(dd / "12_geocas_solved.json", exact)

    # 모든 선언된 점이 풀렸는지 확인
    if constraint_spec:
        declared = set((constraint_spec.get("entities", {}) or {}).get("points", []) or [])
        solved = set((exact.get("points", {}) or {}).keys())
        unsolved = sorted(list(declared - solved))
        if unsolved:
            raise ValueError(
                "GeoCAS could not solve coordinates for: "
                f"{unsolved}. Check ConstraintSpec constraints."
            )

    # GEO 치환 맵
    geo_repls = build_geo_replacements(exact=exact, hint=geometry_hint, decimals=6)
    missing_geo = sorted([k for k in geo_needed if k not in (geo_repls or {})])
    if missing_geo:
        raise ValueError(f"GEO placeholders without mapping: {missing_geo}")

    # 5) CAS (대수 해 계산)
    cas_res = []
    if cg.cas_jobs:
        jobs = [CASJob(**j) for j in cg.cas_jobs]
        cas_res = run_cas(jobs)
    if _is_debug() and dd:
        _dump_json(dd / "13_cas_results.json", cas_res)

    # 6) GEO → CAS 순서로 치환 (★ geo_replacements 필수!)
    if geo_needed or cas_needed:
        final = fill_placeholders(
            draft=cg.manim_code_draft,
            repls=cas_res,
            geo_replacements=geo_repls,
            on_missing="fail_build",
        )
        code = final.manim_code_final
    else:
        code = cg.manim_code_draft

    if _is_debug() and dd:
        (dd / "20_manim_code_filled.py").write_text(code, encoding="utf-8")

    return code


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m pipelines.e2e <image_path> <ocr_json>")
        sys.exit(1)

    image_path, ocr_json = sys.argv[1], sys.argv[2]
    doc = load_problem(image_path, ocr_json)
    code = run_pipeline(doc)

    out_root = Path("ManimcodeOutput")
    out_root.mkdir(exist_ok=True)
    problem_name = Path(image_path).stem if image_path else "unknown"
    problem_dir = out_root / problem_name
    problem_dir.mkdir(exist_ok=True)

    out_py = problem_dir / f"{problem_name}.py"
    out_py.write_text(code, encoding="utf-8")

    readme = problem_dir / "README.md"
    readme.write_text(
        f"# {problem_name} Manim Code\n\n"
        "## 실행 방법\n\n"
        f"```bash\nmanim {problem_name}.py -pql\n```\n",
        encoding="utf-8",
    )
    print(f"[OK] Saved: {out_py}")
