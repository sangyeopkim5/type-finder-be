import pathlib, sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from apps.router.router import route_problem
from libs.schemas import ProblemDoc, OCRItem


def test_router_flags():
    doc = ProblemDoc(
        items=[
            OCRItem(bbox=[0,0,1,1], category="Text"),
            OCRItem(bbox=[0,0,1,1], category="Formula"),
            OCRItem(bbox=[0,0,1,1], category="List"),
        ]
    )
    res = route_problem(doc)
    assert res["mode"] == "vision"
    assert res["has_formula"] is True
    assert res["has_list"] is True


def test_router_picture():
    doc = ProblemDoc(items=[OCRItem(bbox=[0,0,1,1], category="Picture")])
    res = route_problem(doc)
    assert res["has_picture"] is True
    assert res["mode"] == "vision"


def test_router_text_only():
    doc = ProblemDoc(items=[OCRItem(bbox=[0,0,1,1], category="Text")])
    res = route_problem(doc)
    assert res == {
        "mode": "text",
        "has_formula": False,
        "has_picture": False,
        "has_list": False,
    }
