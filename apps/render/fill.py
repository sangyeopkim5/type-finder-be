from typing import List, Optional, Dict, Literal, Set
import logging
import re
from libs.schemas import CASResult, RenderOutput

logger = logging.getLogger(__name__)


def fill_placeholders(
    draft: str,
    repls: List[CASResult],
    geo_replacements: Optional[Dict[str, str]] = None,
    on_missing: Literal["fail_build", "warn_token"] = "fail_build",
) -> RenderOutput:
    """
    Replace GEO and CAS placeholders in ``draft``.

    Order of operations:
      1) GEO placeholders: [[GEO:point:A]], [[GEO:angle:B-A-C]], [[GEO:angleflag:B-A-C]], [[GEO:tangent_dir:D]]
         - Values come from ``geo_replacements``, whose keys are WITHOUT the "GEO:" prefix.
           e.g. {"point:A": "(1.0, 0.0)", "angle:B-A-C": "47", "angleflag:B-A-C": "False"}
      2) CAS placeholders: [[CAS:ID]] -> wraps LaTeX as "{<latex>}"

    Unreplaced placeholders cause a ValueError, to fail fast for accuracy
    (unless ``on_missing='warn_token'`` for GEO placeholders). If there are
    no placeholders at all, returns the original draft unchanged.
    """

    # Fast path: return as-is when no placeholders of any kind
    if "[[CAS:" not in draft and "[[GEO:" not in draft:
        return RenderOutput(manim_code_final=draft)

    code = draft

    # ---------- 1) GEO replacements ----------
    if geo_replacements:
        for k, v in geo_replacements.items():
            # k examples: "point:A", "angle:B-A-C", "angleflag:B-A-C", "tangent_dir:D"
            placeholder = f"[[GEO:{k}]]"
            code = code.replace(placeholder, str(v))

    # After GEO pass, make sure nothing remains
    if "[[GEO:" in code:
        # Pinpoint the first remaining token for better debugging
        start = code.find("[[GEO:")
        end = code.find("]]", start)
        token = code[start : (end + 2 if end != -1 else start + 10)]
        if on_missing == "fail_build":
            raise ValueError(f"Unreplaced GEO placeholder remains: {token}")
        logger.warning("Unreplaced GEO placeholder: %s", token)

    # ---------- 2) CAS replacements (existing logic) ----------
    seen = set()
    for r in repls:
        if r.id in seen:
            logging.warning(f"duplicate CAS id {r.id}")
            continue
        seen.add(r.id)
        code = code.replace(f"[[CAS:{r.id}]]", "{" + r.result_tex + "}")

    if "[[CAS:" in code:
        # Pinpoint the first remaining token for better debugging
        start = code.find("[[CAS:")
        end = code.find("]]", start)
        token = code[start : (end + 2 if end != -1 else start + 10)]
        raise ValueError(f"Unreplaced CAS placeholder remains: {token}")

    return RenderOutput(manim_code_final=code)


# ------------------------
# Placeholder utilities
# ------------------------
def collect_geo_placeholders(draft: str) -> Set[str]:
    """
    Return the set of GEO keys found in the draft, e.g. {"point:A", "angle:B-A-C"}.
    """
    keys: Set[str] = set()
    for m in re.finditer(r"\[\[GEO:([^\]]+)\]\]", draft):
        key = m.group(1).strip()
        if key:
            keys.add(key)
    return keys


def collect_cas_placeholders(draft: str) -> Set[str]:
    """
    Return the set of CAS IDs found in the draft, e.g. {"S1", "TOTAL"}.
    Only literal tokens of the form [[CAS:ID]] are collected.
    """
    ids: Set[str] = set()
    for m in re.finditer(r"\[\[CAS:([A-Za-z0-9_]+)\]\]", draft):
        ids.add(m.group(1))
    return ids


def detect_invalid_cas_token_patterns(draft: str) -> List[str]:
    """
    Heuristically detect dynamic or malformed CAS tokens such as
    "[[CAS:" + id + "]]" or f"[[CAS:{id}]]" inside code strings.
    Returns a list of offending snippets for diagnostics.
    """
    offenders: List[str] = []
    # String concatenation like "[[CAS:" + id + "]]"
    for m in re.finditer(r"\[\[CAS:\s*\"?\s*\+", draft):
        start = max(0, m.start() - 20)
        end = min(len(draft), m.end() + 20)
        offenders.append(draft[start:end])
    # f-string interpolation like f"...[[CAS:{id}]]..."
    for m in re.finditer(r"f[\'\"](?:[^\n\r]*?)\[\[CAS:\{", draft):
        start = max(0, m.start() - 20)
        end = min(len(draft), m.end() + 20)
        offenders.append(draft[start:end])
    return offenders


def extract_geo_labels(keys: Set[str]) -> Set[str]:
    """
    From GEO placeholder keys like "point:A", "angle:B-A-C", "tangent_dir:D",
    collect the set of point labels referenced: {"A","B","C","D"}.
    """
    labels: Set[str] = set()
    for key in keys:
        try:
            if key.startswith("point:"):
                labels.add(key.split(":", 1)[1].strip())
            elif key.startswith("tangent_dir:"):
                labels.add(key.split(":", 1)[1].strip())
            elif key.startswith("angle:") or key.startswith("angleflag:"):
                rest = key.split(":", 1)[1]
                for part in rest.split("-"):
                    part = part.strip()
                    if part:
                        labels.add(part)
        except Exception:
            # be permissive; malformed keys are handled elsewhere
            continue
    return {l for l in labels if l}
