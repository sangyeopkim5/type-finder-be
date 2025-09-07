from typing import Dict
from libs.schemas import ProblemDoc


PICTURE_CATS = {"Picture", "Diagram", "Graph", "Figure"}
LIST_CATS = {"List", "List-item", "Choice", "Options"}


def route_problem(doc: ProblemDoc) -> Dict:
    has_formula = any(i.category == "Formula" for i in doc.items)
    has_diagram = any(i.category in PICTURE_CATS for i in doc.items)
    has_list = any(i.category in LIST_CATS for i in doc.items)
    mode = "vision" if (bool(doc.image_path) or has_formula) else "text"
    return {
        "mode": mode,
        "has_formula": has_formula,
        "has_diagram": has_diagram,
        "has_list": has_list,
    }

