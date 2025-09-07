from __future__ import annotations

from typing import List, Dict, Optional, Any, Tuple
import math
import re

from sympy import (
    simplify,
    latex,
    Rational,
    symbols,
    sin,
    cos,
    tan,
    sqrt,
    expand,
    factor,
    pi,
    Function,
    atan2 as s_atan2,
    Eq,
    nsolve,
)
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)
from sympy import Matrix
from libs.schemas import CASJob, CASResult


# =====================================================================
# Algebra CAS (기존)
# =====================================================================

SAFE_FUNCS = {
    "simplify": simplify,
    "Rational": Rational,
   
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "sqrt": sqrt,
    "expand": expand,
    "factor": factor,
    "pi": pi,
}


def run_cas(jobs: List[CASJob]) -> List[CASResult]:
    out: List[CASResult] = []
    for j in jobs:
        expr_s = j.expr.strip()
        try:
            # allow only whitelisted function calls before parsing
            for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", expr_s):
                name = match.group(1)
                if name not in SAFE_FUNCS:
                    raise ValueError(f"function {name} not allowed")

            transformations = standard_transformations + (implicit_multiplication_application,)
            expr = parse_expr(expr_s, transformations=transformations, local_dict=SAFE_FUNCS)

            for f in expr.atoms(Function):
                name = f.func.__name__
                if name not in SAFE_FUNCS:
                    raise ValueError(f"function {name} not allowed")

            val = simplify(expr)
            out.append(CASResult(id=j.id, result_tex=latex(val), result_py=str(val)))
        except Exception as e:
            import traceback
            error_detail = (
                f"CAS error in {j.id}: {e}\nExpression: {expr_s}\nTraceback: {traceback.format_exc()}"
            )
            raise ValueError(error_detail)
    return out


# =====================================================================
# GeoCAS (강건성 강화판)
# - ConstraintSpec(JSON) + GeometryHint(JSON|None) → ExactGeometry(dict)
# =====================================================================

def _rad(deg: float) -> float:
    return float(deg) * math.pi / 180.0


def _wrap_pipi(t: float) -> float:
    while t <= -math.pi:
        t += 2 * math.pi
    while t > math.pi:
        t -= 2 * math.pi
    return t


def _oriented_angle(u: Matrix, v: Matrix):
    """유향각 atan2(det, dot) (심볼릭). u, v: 2D sympy Matrix"""
    det = u[0] * v[1] - u[1] * v[0]
    dot = u.dot(v)
    return s_atan2(det, dot)  # (-pi, pi]


def _parse_angle_triplet(triplet: Any) -> tuple[str, str, str]:
    """
    ["B","A","C"] 또는 "BAC"을 (B,A,C)로 반환.
    """
    if isinstance(triplet, (list, tuple)) and len(triplet) == 3:
        return str(triplet[0]), str(triplet[1]), str(triplet[2])
    if isinstance(triplet, str) and len(triplet) == 3:
        return triplet[0], triplet[1], triplet[2]
    raise ValueError(f"invalid angle triple: {triplet}")


def _build_point_labels(entities: Dict[str, Any], constraints: List[Dict[str, Any]]) -> List[str]:
    pts = []
    if isinstance(entities, dict):
        if "points" in entities and isinstance(entities["points"], list):
            pts = [str(p) for p in entities["points"]]
    if not pts:
        found = set()
        for c in constraints:
            if not isinstance(c, dict):
                continue
            if "points" in c and isinstance(c["points"], list):
                for p in c["points"]:
                    found.add(str(p))
            if "angle" in c:
                B, A, C = _parse_angle_triplet(c["angle"])
                found.update([A, B, C])
            if "point" in c:
                found.add(str(c["point"]))
        pts = sorted(found)
    return pts


# -------------------------
# 초기값 생성(강화)
# -------------------------

def _initial_guess_from_hint(point_labels: List[str], hint: Optional[Dict]) -> Dict[str, float]:
    """
    GeometryHint(points_hint)에서 각 점의 극각 초기값을 추정.
    없으면 0, 2π/N 균등 배치.
    """
    t0: Dict[str, float] = {}
    if hint and isinstance(hint, dict):
        pts = hint.get("points_hint", [])
        if isinstance(pts, list):
            for ph in pts:
                try:
                    lbl = str(ph.get("id"))
                    x, y = ph.get("xy", [None, None])
                    if lbl and x is not None and y is not None:
                        t0[lbl] = math.atan2(float(y), float(x))
                except Exception:
                    pass
    missing = [p for p in point_labels if p not in t0]
    if missing:
        n = max(1, len(point_labels))
        for k, lbl in enumerate(missing):
            t0[lbl] = 2 * math.pi * (k / n)
    return t0


def _apply_arc_sweep_hints(t0: Dict[str, float], constraints: List[Dict[str, Any]], hint: Optional[Dict]) -> Dict[str, float]:
    """
    arc_direction_hint (ConstraintSpec) 또는 GeometryHint.arcs의 sweep 정보를 사용해
    초기값의 상대적인 순서를 조정하여 ccw/cw를 맞춘다.
    """
    t = dict(t0)

    # 1) ConstraintSpec에 arc_direction_hint가 명시된 경우
    for c in constraints:
        if isinstance(c, dict) and c.get("type") == "arc_direction_hint":
            arc = c.get("arc", [])
            sweep = c.get("sweep", "ccw")
            if isinstance(arc, list) and len(arc) == 2:
                p, q = str(arc[0]), str(arc[1])
                if p in t and q in t:
                    if sweep == "ccw" and t[q] <= t[p]:
                        t[q] = t[p] + 0.8
                    if sweep == "cw" and t[q] >= t[p]:
                        t[q] = t[p] - 0.8

    # 2) GeometryHint.arcs를 사용한 힌트(있다면)
    if hint and isinstance(hint, dict):
        arcs = hint.get("arcs", [])
        if isinstance(arcs, list):
            # 여기서는 단순히 sweep 방향을 전체적으로 밀어주는 정도로만 활용
            # (라벨-호 연결 매핑은 문제/파서 수준에서 제공될 때 더 강하게 사용 가능)
            for a in arcs:
                sweep = a.get("sweep", None)
                if sweep == "ccw":
                    # 전체 각도를 약간 증가 방향으로 벌림
                    for k in t.keys():
                        t[k] = t[k] + 0.05
                elif sweep == "cw":
                    for k in t.keys():
                        t[k] = t[k] - 0.05
    return t


def _generate_seed_variants(
    base_t0: Dict[str, float],
    point_labels: List[str],
    angle_specs: List[Tuple[str, str, str, float, Optional[str]]],
    constraints: List[Dict[str, Any]],
    hint: Optional[Dict],
) -> List[Dict[str, float]]:
    """
    멀티 시작점 생성:
      - 기본 t0
      - arc sweep/acute/obtuse 힌트를 반영한 확장 시드
      - 소규모 난조(perturbation)로 국소해 탈출 지원
    """
    seeds: List[Dict[str, float]] = []

    # base
    seeds.append(dict(base_t0))

    # arc sweep 반영
    t_sweep = _apply_arc_sweep_hints(base_t0, constraints, hint)
    seeds.append(dict(t_sweep))

    # acute/obtuse 선호 반영: A 기준으로 B, C를 멀리/가깝게 벌려줌
    for (B, A, C, deg, prefer) in angle_specs:
        t2 = dict(t_sweep)
        if A in t2 and B in t2 and C in t2:
            if prefer == "obtuse":
                # obtuse 선호 → 두 팔을 멀리
                t2[B] = t2[A] + abs(t2[B] - t2[A]) + 0.6
                t2[C] = t2[A] - abs(t2[C] - t2[A]) - 0.6
            elif prefer == "acute":
                # acute 선호 → 두 팔을 가깝게
                t2[B] = t2[A] + 0.2
                t2[C] = t2[A] - 0.2
            seeds.append(t2)

    # 소규모 난조 시드(국소해 탈출)
    if point_labels:
        labels = [lbl for lbl in point_labels]
        for j in range(min(3, len(labels))):
            t_noise = dict(t_sweep)
            for k, lbl in enumerate(labels):
                t_noise[lbl] = t_noise[lbl] + (0.15 if (k + j) % 2 == 0 else -0.15)
            seeds.append(t_noise)

    # wrap
    for s in seeds:
        for k in s.keys():
            s[k] = _wrap_pipi(s[k])

    # 중복 제거
    uniq: List[Dict[str, float]] = []
    seen = set()
    for s in seeds:
        key = tuple(round(s[k], 3) for k in sorted(s.keys()))
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return uniq


# -------------------------
# 메인 GeoCAS
# -------------------------

def run_geocas(constraint_spec: Optional[Dict] = None,
               hint: Optional[Dict] = None) -> Dict:
    """
    ExactGeometry dict 반환:
    {
      "frame": "unit_circle",
      "circle": {"center":[0.0,0.0], "radius":1.0},
      "points": {"A":[x,y], ...},
      "angles": {"BAC":{"deg":47,"obtuse":False}, ...},
      "tangent_dirs": {"D":[tx,ty], ...}
    }
    """
    exact = {
        "frame": "unit_circle",
        "circle": {"center": [0.0, 0.0], "radius": 1.0},
        "points": {},
        "angles": {},
        "tangent_dirs": {},
    }

    if not constraint_spec or "constraints" not in constraint_spec:
        return exact

    constraints = constraint_spec.get("constraints", [])
    entities = constraint_spec.get("entities", {})

    # 1) 라벨 목록
    point_labels = _build_point_labels(entities, constraints)
    if not point_labels:
        return exact

    # 2) 변수 및 좌표 정의
    t_syms = {lbl: symbols(f"t_{lbl}", real=True) for lbl in point_labels}
    P = {lbl: Matrix([cos(t_syms[lbl]), sin(t_syms[lbl])]) for lbl in point_labels}

    # 3) 제약 수집
    eqs = []
    ref_lbl = point_labels[0]  # 회전 게이지 고정
    eqs.append(Eq(t_syms[ref_lbl], 0))

    angle_specs: List[Tuple[str, str, str, float, Optional[str]]] = []  # (B,A,C,deg,prefer)
    tangent_points = set()

    for c in constraints:
        if not isinstance(c, dict):
            continue
        ctype = c.get("type")

        if ctype == "concyclic":
            # 단위원 가정이라 별도 방정식 불필요
            continue

        if ctype == "angle_value":
            B, A, C = _parse_angle_triplet(c.get("angle"))
            deg = float(c.get("deg"))
            prefer = c.get("prefer", None)  # "acute"|"obtuse"|None
            angle_specs.append((B, A, C, deg, prefer))

            # 기본 방정식(미분 가능성 위해 abs 유지 / 다중 시드로 보완)
            u = P[B] - P[A]
            v = P[C] - P[A]
            theta = _oriented_angle(u, v)  # (-pi, pi]
            eqs.append(Eq(abs(theta), _rad(deg)))

        if ctype == "tangent":
            lbl = str(c.get("point"))
            if lbl in t_syms:
                tangent_points.add(lbl)

        # arc_direction_hint는 초기값 시드 생성에서 활용

    # 4) 초기값 세트(강건성용 다중 시드)
    base_t0 = _initial_guess_from_hint(point_labels, hint)
    seed_list = _generate_seed_variants(base_t0, point_labels, angle_specs, constraints, hint)

    # 5) nsolve 반복 시도 → 잔차 최소 해 선택
    unknown_syms = [t_syms[lbl] for lbl in point_labels if lbl != ref_lbl]
    eqs_to_solve = [e for e in eqs if not (e.lhs == t_syms[ref_lbl])]
    best = None  # (residual, solved_dict)

    if unknown_syms:
        for seed in seed_list:
            x0 = [seed[lbl] for lbl in point_labels if lbl != ref_lbl]
            try:
                sol_vec = nsolve([e.lhs - e.rhs for e in eqs_to_solve], unknown_syms, x0, tol=1e-14, maxsteps=200)
                solved = {ref_lbl: 0.0}
                for sym, val in zip(unknown_syms, list(sol_vec)):
                    solved[str(sym)[2:]] = _wrap_pipi(float(val))
                # residual 측정
                res = 0.0
                for (B, A, C, deg, _pref) in angle_specs:
                    tB, tA, tC = solved[B], solved[A], solved[C]
                    u = (math.cos(tB) - math.cos(tA), math.sin(tB) - math.sin(tA))
                    v = (math.cos(tC) - math.cos(tA), math.sin(tC) - math.sin(tA))
                    theta = math.atan2(u[0]*v[1] - u[1]*v[0], u[0]*v[0] + u[1]*v[1])
                    res += (abs(theta) - _rad(deg)) ** 2
                cand = (res, solved)
                if (best is None) or (cand[0] < best[0]):
                    best = cand
            except Exception:
                # 실패 시 다음 시드로
                continue

        # 모든 시드 실패 → 폴백(초기값)
        if best is None:
            best = (1e9, {lbl: (0.0 if lbl == ref_lbl else base_t0.get(lbl, 0.0)) for lbl in point_labels})
        solved = best[1]
    else:
        solved = {ref_lbl: 0.0}

    # 6) 좌표/각/접선 계산 및 플래그(acute/obtuse) 재평가
    exact_pts: Dict[str, List[float]] = {}
    for lbl, tval in solved.items():
        exact_pts[lbl] = [float(math.cos(tval)), float(math.sin(tval))]
    exact["points"] = exact_pts

    # angle_value 기록 (prefer 반영: 실제 각이 선호와 맞지 않으면 보각 옵션 체크)
    for (B, A, C, deg, prefer) in angle_specs:
        tB, tA, tC = solved[B], solved[A], solved[C]
        u = (math.cos(tB) - math.cos(tA), math.sin(tB) - math.sin(tA))
        v = (math.cos(tC) - math.cos(tA), math.sin(tC) - math.sin(tA))
        theta = math.atan2(u[0]*v[1] - u[1]*v[0], u[0]*v[0] + u[1]*v[1])
        theta_abs = abs(theta)

        # obtuse 판정: prefer 우선, 없으면 값으로 유추
        if prefer == "obtuse":
            obtuse = True
        elif prefer == "acute":
            obtuse = False
        else:
            obtuse = (theta_abs > math.pi / 2)

        key = f"{B}{A}{C}"
        exact["angles"][key] = {"deg": float(deg), "obtuse": bool(obtuse)}

    # tangent 방향
    for lbl in set(tangent_points):
        if lbl in solved:
            tval = solved[lbl]
            tx, ty = -math.sin(tval), math.cos(tval)
            exact["tangent_dirs"][lbl] = [float(tx), float(ty)]

    return exact
