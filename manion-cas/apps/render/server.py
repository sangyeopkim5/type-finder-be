from fastapi import APIRouter, HTTPException
from libs.schemas import RenderInput
from .fill import fill_placeholders

router = APIRouter(prefix="/render", tags=["render"])

@router.post("/fill")
def fill_endpoint(payload: RenderInput):
    try:
        return fill_placeholders(payload.manim_code_draft, payload.replacements)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
