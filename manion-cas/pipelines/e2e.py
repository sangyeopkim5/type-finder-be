import json
import sys
from typing import List

from libs.schemas import ProblemDoc, CASJob
from apps.codegen.codegen import generate_manim
from apps.cas.compute import run_cas
from apps.render.fill import fill_placeholders


def run_pipeline(doc: ProblemDoc) -> str:
    """Run the end-to-end pipeline locally.

    The function generates Manim code from ``doc`` using the codegen module,
    optionally executes CAS jobs, and fills placeholders. When the code
    generation step produces no CAS jobs, the intermediate code is returned
    unchanged without calling the CAS or render steps.
    """

    cg = generate_manim(doc)

    # If there are no CAS jobs we can return the draft code immediately.
    if not cg.cas_jobs:
        return cg.manim_code_draft

    jobs: List[CASJob] = [CASJob(**j) for j in cg.cas_jobs]
    cas_res = run_cas(jobs)
    final = fill_placeholders(cg.manim_code_draft, cas_res)
    return final.manim_code_final


if __name__ == "__main__":
    img = sys.argv[1]
    js = sys.argv[2]
    items = json.load(open(js, "r", encoding="utf-8"))
    doc = ProblemDoc(items=items, image_path=img)
    code = run_pipeline(doc)
    print(code.strip())
