# libs/layout.py
from __future__ import annotations
from typing import List, Sequence, Any, Dict, Optional, Tuple
from pathlib import Path
import subprocess
import tempfile
import math
import xml.etree.ElementTree as ET
import logging

# ---------- Optional deps (graceful import) ----------
def _try_import(mod):
    try:
        return __import__(mod)
    except Exception:
        return None

np = _try_import("numpy")
cv2 = _try_import("cv2")
PIL = _try_import("PIL.Image")
spt = _try_import("svgpathtools")
sp_opt = _try_import("scipy.optimize")
shapely_mod = _try_import("shapely")
if shapely_mod:
    from shapely.geometry import LineString, Point as ShPoint  # noqa: F401

logger = logging.getLogger(__name__)

# ============================================================
# 튜닝 상수
# ============================================================
CANNY_LOW, CANNY_HIGH = 50, 150
HOUGH_LINE_TH = 60
HOUGH_LINE_MINLEN, HOUGH_LINE_MAXGAP = 40, 8
HOUGH_CIRCLE_DP, HOUGH_CIRCLE_MINDIST = 1.3, 30
HOUGH_CIRCLE_PARAM1, HOUGH_CIRCLE_PARAM2 = 120, 35
HOUGH_CIRCLE_MINR, HOUGH_CIRCLE_MAXR = 15, 0

POINT_MERGE_EPS = 1.5   # px 병합 임계
ROUND_PT = 3            # 좌표 반올림 자리수
ROUND_ANG = 5           # 각 반올림 자리수

# ============================================================
# 읽기 순서 (원본 유지)
# ============================================================
def _bbox(item: Any) -> Sequence[float]:
    if hasattr(item, "bbox"):
        return item.bbox
    return item["bbox"]

def reading_order(items: List[Any]) -> List[Any]:
    if not items:
        return []
    centers = []
    heights = []
    for it in items:
        x1, y1, x2, y2 = _bbox(it)
        centers.append((y1 + y2) / 2)
        heights.append(y2 - y1)
    avg_h = sum(heights) / len(heights)
    tol = avg_h * 0.7
    row_centers: List[float] = []
    assigned: List[tuple[Any, int]] = []
    for it, yc in sorted(zip(items, centers), key=lambda t: t[1]):
        for idx, rc in enumerate(row_centers):
            if abs(yc - rc) <= tol:
                row_centers[idx] = (rc + yc) / 2
                assigned.append((it, idx))
                break
        else:
            row_centers.append(yc)
            assigned.append((it, len(row_centers) - 1))

    def _area(it: Any) -> float:
        x1, y1, x2, y2 = _bbox(it)
        return (x2 - x1) * (y2 - y1)

    def _x1(it: Any) -> float: return _bbox(it)[0]
    def _y1(it: Any) -> float: return _bbox(it)[1]

    ordered = sorted(assigned, key=lambda t: (t[1], _x1(t[0]), _y1(t[0]), _area(t[0])))
    return [it for it, _ in ordered]

# ============================================================
# 유틸: 가까운 포인트 병합/스냅
# ============================================================
def _merge_close_points(pts: List[Tuple[float, float]], eps: float = POINT_MERGE_EPS) -> List[Tuple[float, float]]:
    if not pts:
        return []
    out: List[Tuple[float, float]] = []
    for (x, y) in pts:
        merged = False
        for i, (X, Y) in enumerate(out):
            if (x - X) ** 2 + (y - Y) ** 2 <= eps ** 2:
                out[i] = ((X + x) / 2.0, (Y + y) / 2.0)
                merged = True
                break
        if not merged:
            out.append((x, y))
    return out

def _round_xy(x: float, y: float, nd: int = ROUND_PT) -> Tuple[float, float]:
    return round(float(x), nd), round(float(y), nd)

# ============================================================
# SVG 벡터화 → GeometryHint
# ============================================================
def _has_bin(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        logger.warning("Binary '%s' not found; geometry hint extraction may be degraded.", cmd)
        return False

def _bitmap_to_svg_via_inkscape(src: Path, dst_svg: Path) -> bool:
    try_cmds = [
        ["inkscape", str(src), f"--export-filename={dst_svg}",
         "--actions=EditSelectAll;SelectionTraceBitmap;FileSave;FileClose"],
        ["inkscape", str(src), f"--export-filename={dst_svg}",
         "--actions=org.inkscape.trace.bitmap;FileSave;FileClose"],
        ["inkscape", str(src), "--export-plain-svg", str(dst_svg)],
    ]
    for cmd in try_cmds:
        try:
            subprocess.run(cmd, check=True)
            if dst_svg.exists() and dst_svg.stat().st_size > 0:
                return True
        except Exception:
            continue
    return False

def _bitmap_to_svg_via_potrace(src: Path, dst_svg: Path) -> bool:
    if not PIL:
        return False
    try:
        tmp_pbm = dst_svg.with_suffix(".pbm")
        img = PIL.Image.open(src).convert("L")
        img = img.point(lambda p: 255 if p > 200 else 0).convert("1")
        img.save(tmp_pbm)
        subprocess.run(["potrace", "-s", "-o", str(dst_svg), str(tmp_pbm)], check=True)
        tmp_pbm.unlink(missing_ok=True)
        return dst_svg.exists() and dst_svg.stat().st_size > 0
    except Exception:
        return False

def _parse_svg_paths(svg_path: Path) -> Dict:
    out = {"circles": [], "lines": [], "arcs": [], "points_hint": []}
    if spt:
        try:
            paths, attrs, svg_attr = spt.svg2paths2(str(svg_path))
            for p, a in zip(paths, attrs):
                for seg in p:
                    if isinstance(seg, spt.Line):
                        x1, y1 = seg.start.real, seg.start.imag
                        x2, y2 = seg.end.real, seg.end.imag
                        out["lines"].append({"id": f"l_{len(out['lines'])+1}",
                                             "p1": list(_round_xy(x1, y1)),
                                             "p2": list(_round_xy(x2, y2))})
                        out["points_hint"] += [
                            {"id": f"P{len(out['points_hint'])+1}", "xy": list(_round_xy(x1, y1))},
                            {"id": f"P{len(out['points_hint'])+1}", "xy": list(_round_xy(x2, y2))}
                        ]
                    elif isinstance(seg, spt.Arc):
                        cx, cy = seg.center.real, seg.center.imag
                        rx, ry = seg.radius
                        r = float((rx + ry) / 2.0) if rx and ry else float(rx or ry)
                        th_s = math.atan2(seg.start.imag - cy, seg.start.real - cx)
                        th_e = math.atan2(seg.end.imag - cy, seg.end.real - cx)
                        sweep = "ccw" if seg.sweep else "cw"
                        circ_id = f"c_{len(out['circles'])+1}"
                        out["circles"].append({"id": circ_id, "center": list(_round_xy(cx, cy)),
                                               "radius": round(float(r), ROUND_ANG)})
                        out["arcs"].append({"id": f"a_{len(out['arcs'])+1}",
                                            "circle": circ_id,
                                            "theta_start": round(float(th_s), ROUND_ANG),
                                            "theta_end": round(float(th_e), ROUND_ANG),
                                            "sweep": sweep})
                        out["points_hint"] += [
                            {"id": f"P{len(out['points_hint'])+1}", "xy": list(_round_xy(seg.start.real, seg.start.imag))},
                            {"id": f"P{len(out['points_hint'])+1}", "xy": list(_round_xy(seg.end.real, seg.end.imag))}
                        ]
        except Exception:
            pass

    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        for c in root.iter(f"{ns}circle"):
            cx = float(c.attrib.get("cx", "0"))
            cy = float(c.attrib.get("cy", "0"))
            r = float(c.attrib.get("r", "0"))
            circ_id = f"c_{len(out['circles'])+1}"
            out["circles"].append({"id": circ_id, "center": list(_round_xy(cx, cy)), "radius": round(r, ROUND_ANG)})
            out["points_hint"].append({"id": f"P{len(out['points_hint'])+1}", "xy": list(_round_xy(cx, cy))})
    except Exception:
        pass

    pts = [(ph["xy"][0], ph["xy"][1]) for ph in out["points_hint"]]
    pts = _merge_close_points(pts, POINT_MERGE_EPS)
    out["points_hint"] = [{"id": f"P{i+1}", "xy": [round(x, ROUND_PT), round(y, ROUND_PT)]} for i, (x, y) in enumerate(pts)]
    return out

def _fallback_detect_with_opencv(src: Path) -> Dict:
    out = {"circles": [], "lines": [], "arcs": [], "points_hint": []}
    if not (cv2 and np):
        logger.warning("OpenCV or numpy not available; geometry hint extraction will return empty hints.")
        return out
    try:
        data = np.fromfile(str(src), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    except Exception:
        img = None
    if img is None:
        return out
    img = cv2.GaussianBlur(img, (3, 3), 0)
    edges = cv2.Canny(img, CANNY_LOW, CANNY_HIGH, apertureSize=3)

    lines = cv2.HoughLinesP(edges, 1, math.pi/180,
                            threshold=HOUGH_LINE_TH,
                            minLineLength=HOUGH_LINE_MINLEN,
                            maxLineGap=HOUGH_LINE_MAXGAP)
    if lines is not None:
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            p1 = _round_xy(int(x1), int(y1)); p2 = _round_xy(int(x2), int(y2))
            out["lines"].append({"id": f"l_{len(out['lines'])+1}", "p1": list(p1), "p2": list(p2)})
            out["points_hint"] += [{"id": f"P{len(out['points_hint'])+1}", "xy": list(p1)},
                                   {"id": f"P{len(out['points_hint'])+1}", "xy": list(p2)}]

    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT,
                               dp=HOUGH_CIRCLE_DP,
                               minDist=HOUGH_CIRCLE_MINDIST,
                               param1=HOUGH_CIRCLE_PARAM1,
                               param2=HOUGH_CIRCLE_PARAM2,
                               minRadius=HOUGH_CIRCLE_MINR,
                               maxRadius=HOUGH_CIRCLE_MAXR)
    if circles is not None:
        for (x, y, r) in circles.reshape(-1, 3):
            center = _round_xy(float(x), float(y))
            out["circles"].append({"id": f"c_{len(out['circles'])+1}",
                                   "center": list(center),
                                   "radius": round(float(r), ROUND_ANG)})
            out["points_hint"].append({"id": f"P{len(out['points_hint'])+1}", "xy": list(center)})

    pts = [(ph["xy"][0], ph["xy"][1]) for ph in out["points_hint"]]
    pts = _merge_close_points(pts, POINT_MERGE_EPS)
    out["points_hint"] = [{"id": f"P{i+1}", "xy": [round(x, ROUND_PT), round(y, ROUND_PT)]} for i, (x, y) in enumerate(pts)]
    return out

# ---------- 추가: 라벨 추출/사각형 코너 검출 ----------
def _extract_label_boxes_from_ocr(
    ocr_json: Optional[List[Dict[str, Any]]]
) -> Dict[str, Tuple[float, float]]:
    """
    OCR JSON에서 한 글자 라벨 "A","B","C","D"의 중심좌표 추출.
    """
    out: Dict[str, Tuple[float, float]] = {}
    if not ocr_json:
        return out
    targets = {"A", "B", "C", "D"}
    for it in ocr_json:
        cat = (it.get("category") or "").lower()
        if cat not in {"text", "formula", "caption"}:
            continue
        txt = (it.get("text") or "").strip()
        if txt in targets and "bbox" in it:
            x1, y1, x2, y2 = it["bbox"]
            cx = 0.5 * (x1 + x2); cy = 0.5 * (y1 + y2)
            out[txt] = (float(cx), float(cy))
    return out

def _detect_quadrilateral_corners_raw(image_path: str) -> Optional[List[Tuple[float, float]]]:
    if cv2 is None or np is None:
        return None
    try:
        # ✅ Windows 한글 경로 안전 읽기
        data = np.fromfile(str(image_path), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        img = None
    if img is None:
        logger.warning("OpenCV imdecode failed: %s", image_path)
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    thr = cv2.medianBlur(thr, 5)
    cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnt = max(cnts, key=cv2.contourArea)
    eps = 0.02 * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, eps, True)
    if len(approx) == 4:
        return [(float(p[0][0]), float(p[0][1])) for p in approx]
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    return [(float(x), float(y)) for (x, y) in box]

def _order_quad_clockwise(pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if len(pts) != 4:
        return pts
    pts = list(pts)
    pts_sorted = sorted(pts, key=lambda p: (p[1], p[0]))  # by y then x
    top = sorted(pts_sorted[:2], key=lambda p: p[0])      # left→right
    bottom = sorted(pts_sorted[2:], key=lambda p: p[0])   # left→right
    TL, TR = top[0], top[1]
    BL, BR = bottom[0], bottom[1]
    return [TL, BL, BR, TR]  # 시계방향: A,B,C,D 매핑에 사용

# ============================================================
# GeometryHint 추출 (OCR 라벨 매핑 포함)
# ============================================================
def extract_primitives_from_image(
    image_path: Optional[str],
    ocr_json: Optional[List[Dict[str, Any]]] = None,
) -> Dict:
    """
    반환 GeometryHint:
      {"circles":[],"lines":[],"arcs":[],"points_hint":[{"id":"A","xy":[x,y]}, ...]}
    우선순위:
      1) inkscape/potrace 벡터화 + path 파싱
      2) (부가) 사각형 4꼭짓점 검출 → TL,BL,BR,TR
      3) OCR 라벨 A,B,C,D가 있으면 최근접 코너에 배정 (부분 라벨도 허용)
      4) 라벨이 없다면 TL,BL,BR,TR을 A,B,C,D로 자동 할당
    """
    empty = {"circles": [], "lines": [], "arcs": [], "points_hint": []}
    if not image_path:
        return empty

    src = Path(image_path).expanduser().resolve()
    if not src.exists():
        return empty

    # 0) 기본 힌트: 벡터화 → 파싱 / 실패 시 OpenCV 폴백
    with tempfile.TemporaryDirectory() as td:
        dst_svg = Path(td) / "trace.svg"
        if _has_bin("inkscape") and _bitmap_to_svg_via_inkscape(src, dst_svg):
            hint = _parse_svg_paths(dst_svg)
        elif _has_bin("potrace") and _bitmap_to_svg_via_potrace(src, dst_svg):
            hint = _parse_svg_paths(dst_svg)
        else:
            hint = _fallback_detect_with_opencv(src)

    # 1) 사각형 4꼭짓점 탐지
    quad = _detect_quadrilateral_corners_raw(str(src))

    # 2) OCR 라벨 추출
    label_boxes = _extract_label_boxes_from_ocr(ocr_json)

    # 3) points_hint 구성 (라벨 우선)
    labeled_points: Dict[str, Tuple[float, float]] = {}
    if label_boxes:
        if quad:
            for lab, lpt in label_boxes.items():
                idx = int(np.argmin([_euclid_sq(lpt, q) for q in quad])) if np is not None else \
                      min(range(len(quad)), key=lambda k: (lpt[0]-quad[k][0])**2 + (lpt[1]-quad[k][1])**2)
                labeled_points[lab] = quad[idx]
        else:
            labeled_points.update(label_boxes)
    elif quad:
        ordered = _order_quad_clockwise(quad)  # TL,BL,BR,TR
        for lab, pt in zip(["A", "B", "C", "D"], ordered):
            labeled_points[lab] = pt

    # 4) 기존 hint.points_hint에 병합 (중복/근접 병합)
    out_pts = [(ph["xy"][0], ph["xy"][1]) for ph in hint.get("points_hint", [])]
    out_pts = _merge_close_points(out_pts, POINT_MERGE_EPS)
    hint["points_hint"] = [{"id": f"P{i+1}", "xy": [round(x, ROUND_PT), round(y, ROUND_PT)]}
                           for i, (x, y) in enumerate(out_pts)]

    # 5) 라벨 포인트(A,B,C,D) 추가
    for lab, pt in labeled_points.items():
        hint["points_hint"].append({"id": lab, "xy": [round(float(pt[0]), ROUND_PT), round(float(pt[1]), ROUND_PT)]})

    return hint

# ============================================================
# Procrustes 유사변환 / GEO 치환 유틸
# ============================================================
def _collect_point_pairs(exact_points: Dict[str, Sequence[float]], hint: Dict) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    exact_xy: List[Tuple[float, float]] = []
    hint_xy: List[Tuple[float, float]] = []
    points_hint = hint.get("points_hint", []) if hint else []
    hint_map = {str(ph.get("id")): ph.get("xy") for ph in points_hint if "id" in ph and "xy" in ph}
    for label, xy in exact_points.items():
        if label in hint_map and hint_map[label] is not None:
            ex = (float(xy[0]), float(xy[1]))
            hv = (float(hint_map[label][0]), float(hint_map[label][1]))
            exact_xy.append(ex); hint_xy.append(hv)
    return exact_xy, hint_xy

def compute_similarity_transform(exact_points: Dict[str, Sequence[float]], hint: Optional[Dict]):
    if np is None or not hint:
        def identity(p): return (float(p[0]), float(p[1]))
        return identity, {"scale": 1.0, "R": [[1.0, 0.0], [0.0, 1.0]], "t": [0.0, 0.0], "used_labels": []}

    ex_xy, hint_xy = _collect_point_pairs(exact_points, hint)
    if len(ex_xy) < 2:
        def identity(p): return (float(p[0]), float(p[1]))
        return identity, {"scale": 1.0, "R": [[1.0, 0.0], [0.0, 1.0]], "t": [0.0, 0.0], "used_labels": []}

    X = np.asarray(ex_xy, dtype=float); Y = np.asarray(hint_xy, dtype=float)
    Xc = X.mean(axis=0); Yc = Y.mean(axis=0)
    X0 = X - Xc; Y0 = Y - Yc
    U, S, Vt = np.linalg.svd(X0.T @ Y0)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    numer = np.sum(Y0 * (X0 @ R)); denom = np.sum(X0 * X0)
    s = float(numer / denom) if denom else 1.0
    t = Yc - s * (Xc @ R)

    def f(p):
        arr = np.asarray(p, dtype=float)
        out = s * (arr @ R) + t
        return (float(out[0]), float(out[1]))

    return f, {"scale": float(s),
               "R": [[float(R[0, 0]), float(R[0, 1])], [float(R[1, 0]), float(R[1, 1])]],
               "t": [float(t[0]), float(t[1])],
               "used_labels": []}

# ============================================================
# GEO 치환 맵 빌더
# ============================================================
def _fmt_tuple(x: float, y: float, nd: int = 6) -> str:
    return f"({round(float(x), nd)}, {round(float(y), nd)})"

def map_exact_points_to_layout(exact: Dict, hint: Optional[Dict]) -> Dict[str, Tuple[float, float]]:
    points = exact.get("points", {}) if exact else {}
    if not points:
        return {}
    f, _ = compute_similarity_transform(points, hint)
    return {label: f((float(xy[0]), float(xy[1]))) for label, xy in points.items()}

def build_geo_replacements(exact: Dict, hint: Optional[Dict] = None, decimals: int = 6) -> Dict[str, str]:
    """
    [[GEO:*]] 치환 맵 생성:
      - [[GEO:point:A]]         → "(x, y)"
      - [[GEO:angle:B-A-C]]     → "deg"
      - [[GEO:angleflag:B-A-C]] → "True|False"
      - [[GEO:tangent_dir:D]]   → "(tx, ty)"
    """
    repl: Dict[str, str] = {}

    mapped = map_exact_points_to_layout(exact, hint)
    for label, (x, y) in mapped.items():
        repl[f"point:{label}"] = _fmt_tuple(x, y, nd=decimals)

    angles = exact.get("angles", {}) if exact else {}
    for key, info in angles.items():
        if not isinstance(key, str) or len(key) < 3:
            continue
        A, B, C = key[1], key[0], key[2]  # "BAC" -> angle:B-A-C
        deg = info.get("deg", None)
        obtuse = bool(info.get("obtuse", False))
        if deg is not None:
            repl[f"angle:{B}-{A}-{C}"] = str(round(float(deg), decimals))
        repl[f"angleflag:{B}-{A}-{C}"] = "True" if obtuse else "False"

    tangents = exact.get("tangent_dirs", {}) if exact else {}
    for label, vec in tangents.items():
        if isinstance(vec, (list, tuple)) and len(vec) >= 2:
            repl[f"tangent_dir:{label}"] = _fmt_tuple(float(vec[0]), float(vec[1]), nd=decimals)

    return repl

# ---------- 내부 헬퍼 ----------
def _euclid_sq(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy
