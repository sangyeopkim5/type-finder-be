from fastapi import APIRouter
from libs.schemas import ProblemDoc
from .codegen import generate_manim


router = APIRouter(prefix="/codegen", tags=["codegen"])


@router.post("/generate")
def generate_endpoint(doc: ProblemDoc):
    return generate_manim(doc)
