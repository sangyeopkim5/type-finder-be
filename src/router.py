# src/router.py
"""
router.py
=========

Deterministic routing policy for Manion CAS-Compiler.

Decides whether an image is needed based on OCR categories & keywords.
"""

from __future__ import annotations
from typing import Any, Dict, List
import re

# dots.ocr 스타일 카테고리 참고:
# ['Caption','Footnote','Formula','List-item','Page-footer','Page-header',
#  'Picture','Section-header','Table','Text','Title']

_POS_KW = re.compile(r"(그림|도형|그래프|좌표|도표|표\s|figure|diagram|plot|chart|table|histogram|scatter|bar chart)", re.I)
_GEO_KW = re.compile(r"(삼각형|사각형|원|타원|벡터|각|∠|△|□|○|⊙|∥|⊥)", re.I)
_NOFIG_KW = re.compile(r"(그림\s*없이|without\s*figure)", re.I)

def infer_routing(segments_json: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return:
      { "need_image": bool, "confidence": float, "reasons": [str] }
    """
    score: float = 0.0
    reasons: List[str] = []

    for seg in segments_json:
        cat = (seg.get("category") or "").strip()
        text = (seg.get("text") or "")

        # Strong layout signals
        if cat == "Picture":
            score += 0.60; reasons.append("has_picture")
        if cat == "Table":
            score += 0.45; reasons.append("has_table")
        if cat == "Caption":
            score += 0.20; reasons.append("has_caption")

        # Text/keyword signals
        if _POS_KW.search(text):
            score += 0.25; reasons.append("mentions_diagram_or_table")
        if _GEO_KW.search(text):
            score += 0.20; reasons.append("mentions_geometry")

        # Labeled points heuristic (A,B,C,O,... 4개 이상)
        tokens = re.findall(r"\b[A-Z](?:['′])?\b", text)
        if len(tokens) >= 4:
            score += 0.10; reasons.append("many_labeled_points")

        # Negative signals
        if _NOFIG_KW.search(text):
            score -= 0.40; reasons.append("explicit_no_figure")

    # Plain algebra only?
    if not any(r in reasons for r in ["has_picture","has_table","has_caption","mentions_diagram_or_table","mentions_geometry","many_labeled_points"]):
        score -= 0.25; reasons.append("plain_algebra_text")

    need_image = score >= 0.50
    conf = round(max(0.0, min(1.0, score)), 2)
    # Borderline note (optional)
    if 0.35 <= conf < 0.50 and not need_image:
        reasons.append("borderline_json_first")

    return {"need_image": need_image, "confidence": conf, "reasons": reasons}
