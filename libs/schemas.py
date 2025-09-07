from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field


# =========================
# OCR / Problem primitives
# =========================

class OCRItem(BaseModel):
    """OCR로부터 얻은 한 블록(문장/수식/라벨 등)."""
    bbox: List[int]                       # [x1, y1, x2, y2]
    category: str                         # "text" | "formula" | "figure" | ...
    text: Optional[str] = None            # 인식 텍스트(수식일 경우 LaTeX 등)


class ProblemDoc(BaseModel):
    """
    문제 단위의 입력 문서.
    기존 필드(items, image_path)를 유지하고,
    B+D 병합을 위해 SVG 기반 힌트(geometry_hint)를 옵션으로 추가.
    """
    items: List[OCRItem]
    image_path: Optional[str] = None
    geometry_hint: Optional[Dict[str, Any]] = None  # NEW: SVG 벡터화/적합 결과 힌트


# =========================
# CAS (Algebra)
# =========================

class CASJob(BaseModel):
    """대수식 계산 작업."""
    id: str
    expr: str


class CASResult(BaseModel):
    """대수식 계산 결과."""
    id: str
    result_tex: str                       # LaTeX
    result_py: str                        # SymPy 표현식 문자열


# =========================
# Geometry (NEW)
# =========================

class GeometryHint(BaseModel):
    """
    SVG/벡터화에서 추출된 '모양' 힌트.
    - circles: [{"id":"c1","center":[x,y],"radius":r}]
    - lines:   [{"id":"l1","p1":[x1,y1],"p2":[x2,y2]}]
    - arcs:    [{"id":"a1","circle":"c1","theta_start":..,"theta_end":..,"sweep":"ccw|cw"}]
    - points_hint: [{"id":"A","xy":[x,y]}]
    """
    circles: List[Dict[str, Any]] = Field(default_factory=list)
    lines: List[Dict[str, Any]] = Field(default_factory=list)
    arcs: List[Dict[str, Any]] = Field(default_factory=list)
    points_hint: List[Dict[str, Any]] = Field(default_factory=list)


class ConstraintSpec(BaseModel):
    """
    LLM이 생성하는 기하 제약(진실).
    - template: 장면 템플릿 키(선택)
    - entities: {"circle":"ω","points":["A","B","C","D","E"], ...}
    - constraints: [{"type":"concyclic","points":["A","B","C","D"], "prefer":"acute"}, ...]
    """
    template: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)


class ExactGeometry(BaseModel):
    """
    GeoCAS로 얻은 '정확 해'.
    - frame: "unit_circle" 고정(유사변환 전 표준 좌표계)
    - circle: {"center":[0,0], "radius":1.0}
    - points: {"A":[x,y], ...}
    - angles: {"BAC":{"deg":47,"obtuse":False}, ...}
    - tangent_dirs: {"D":[tx,ty], ...}
    """
    frame: Literal["unit_circle"] = "unit_circle"
    circle: Dict[str, Any]
    points: Dict[str, List[float]] = Field(default_factory=dict)
    angles: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    tangent_dirs: Dict[str, List[float]] = Field(default_factory=dict)


# =========================
# Codegen I/O
# =========================

class CodegenJob(BaseModel):
    """
    코드 생성 단계의 산출물.
    - manim_code_draft: Manim 초안(좌표/각/접선은 [[GEO:*]] placeholder로 남김)
    - cas_jobs: 기존 CAS 작업 리스트
    - constraint_spec: (NEW) GeoCAS를 위한 기하 제약 JSON
    """
    manim_code_draft: str
    cas_jobs: List[Dict[str, Any]] = Field(default_factory=list)
    constraint_spec: Optional[ConstraintSpec] = None


# =========================
# Render I/O
# =========================

class RenderInput(BaseModel):
    """
    렌더 전 치환 입력값.
    - replacements: 기존 CAS 결과 치환 목록
    - geo_replacements: (NEW) [[GEO:*]] → 값 치환 맵
    """
    manim_code_draft: str
    replacements: List[CASResult] = Field(default_factory=list)
    geo_replacements: Optional[Dict[str, str]] = None  # 예: {"point:A": "(1.0, 0.0)"}


class RenderOutput(BaseModel):
    """치환 완료된 최종 Manim 코드."""
    manim_code_final: str
