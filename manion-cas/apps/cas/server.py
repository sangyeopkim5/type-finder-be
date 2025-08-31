from typing import List
from fastapi import APIRouter, HTTPException
from typing import List
from libs.schemas import CASJob
from .compute import run_cas

router = APIRouter(prefix="/cas", tags=["cas"])

@router.post("/run")
def cas_endpoint(jobs: List[CASJob]):
    try:
        return run_cas(jobs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
