from fastapi import APIRouter
from libs.schemas import ProblemDoc
from .router import route_problem

router = APIRouter(prefix="/router", tags=["router"])

@router.post("/route")
def route_endpoint(doc: ProblemDoc):
    return route_problem(doc)
