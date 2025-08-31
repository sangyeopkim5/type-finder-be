from typing import List
import logging
from libs.schemas import CASResult, RenderOutput


def fill_placeholders(draft: str, repls: List[CASResult]) -> RenderOutput:
    code = draft
    seen = set()
    for r in repls:
        if r.id in seen:
            logging.warning(f"duplicate CAS id {r.id}")
            continue
        seen.add(r.id)
        code = code.replace(f"[[CAS:{r.id}]]", "{" + r.result_tex + "}")
    if "[[CAS:" in code:
        raise ValueError("Unreplaced CAS placeholder remains")
    return RenderOutput(manim_code_final=code)

