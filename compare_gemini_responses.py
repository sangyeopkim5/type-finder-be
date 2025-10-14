import io
import json
import os
import pathlib
from typing import Dict, List, Optional

from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_path


# --- Configuration ---
NUM_CALL_ATTEMPTS = 3
OUTPUT_DIR = pathlib.Path("Output/gemini")
MODEL_NAME = "gemini-2.5-pro"
REQUEST_TIMEOUT = 600

PROMPT_TEXT = """
당신은 수학 문제지의 정답 영역을 OCR 기반으로 분석하는 전문가입니다.
주어진 이미지에서 **모든 문제 번호(4자리)**와 **해당 정답**을 완벽히 인식하고,
아래 요구사항을 **단 한 항목도 빠짐없이** 지켜서 JSON 형식으로 출력하세요.

---

📘 [출력 형식 예시]
[
  {"problem_code": "0001", "question_type": "객관식", "answer": "×", "unit_path": "I. Basic Figures/01 Basic Figures", "level": "A"},
  {"problem_code": "0002", "question_type": "객관식", "answer": "○", "unit_path": "I. Basic Figures/01 Basic Figures", "level": "A"},
  {"problem_code": "0012", "question_type": "단답형", "answer": "\\\\overline{PQ}", "unit_path": "I. Basic Figures/01 Basic Figures", "level": "A"}
]

---

🧩 [필수 규칙]

1️⃣ 문제 번호
- 항상 4자리 숫자 ("0001" ~ "9999")
- 빠짐없이 순차적으로 모두 포함해야 함
- 중간 누락 금지 (예: 0119~0123이 비어 있으면 잘못된 출력)

2️⃣ 문제 유형 (question_type)
- 선택형(O, X, 숫자, 기호, (ㄱ)(ㄴ) 등): `"객관식"`
- 나머지: `"단답형"`

3️⃣ 단원 및 단계
- unit_path: 이미지 상단에 표시된 단원명과 소단원명
- level: A, B, C 중 하나 (색상 또는 구역 제목 기준)

4️⃣ 수학 기호는 **반드시 표준 LaTeX**으로 변환
| 의미 | 표기법 |
|------|--------|
| 선분 AB | `\\\\overline{AB}` |
| 직선 AB | `\\\\overleftrightarrow{AB}` |
| 반직선 AB | `\\\\overrightarrow{AB}` |
| 각도 | `\\\\angle` |
| 수직 | `\\\\perp` |
| 평행 | `\\\\parallel` |
| 도(°) | `^\\\\circ` |
| 분수 1/2 | `\\\\frac{1}{2}` |
| 곱셈 기호 | `\\\\times` |
| 괄호 기호 | 그대로 유지: `()`, `[]`, `{}` |

5️⃣ 불필요한 변형 금지
- `"O"`와 `"○"`는 모두 `"○"`로 통일 (객관식 정답)
- `"X"`는 `"×"`로 통일
- 숫자 `"④"` 등 특수번호는 `"4"`로 통일
- `\\degree`, `\\deg` 등은 절대 사용 금지 → 항상 `^\\circ`

6️⃣ 출력 형식
- JSON 배열로 출력 (list)
- LaTeX 내 백슬래시는 반드시 두 번(`\\\\`) 사용
- 문자열 외의 주석, 설명, 자연어 포함 금지

7️⃣ 정확도 우선
- 불확실할 경우 빈칸으로 남기지 말고 **가장 가능성 높은 후보 1개만** 선택
- 오답보다는 누락이 더 큰 오류로 간주되므로, 누락이 발생하지 않도록 전체 번호를 확인

---

🎯 [핵심 목표]
- 문제 번호 전부 인식 (누락 없음)
- LaTeX 완전 통일 (`^\\\\circ` 표기, 기호 통일)
- JSON 구조 오류 없음
- 모든 항목이 위 규칙에 100% 부합
""".strip()


# --- Helpers ---
def load_image_bytes(path: pathlib.Path) -> bytes:
    """Load an image (or first page of PDF) and return PNG bytes."""
    buffer = io.BytesIO()

    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        with Image.open(path) as img:
            img.convert("RGB").save(buffer, format="PNG")
    elif suffix == ".pdf":
        poppler_path = os.getenv("POPPLER_PATH") or None
        kwargs = {}
        if poppler_path:
            kwargs["poppler_path"] = poppler_path
        images = convert_from_path(
            str(path),
            first_page=1,
            last_page=1,
            fmt="png",
            **kwargs,
        )
        if not images:
            raise ValueError("PDF에서 이미지를 변환할 수 없습니다.")
        images[0].convert("RGB").save(buffer, format="PNG")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {path.suffix}")

    return buffer.getvalue()


def sanitize_json_text(raw_text: str) -> str:
    """Remove Markdown fences and trim to JSON array if present."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket != -1:
        return cleaned[first_bracket : last_bracket + 1]
    return cleaned


def prepare_image_for_model(image_bytes: bytes) -> Image.Image:
    """Create a PIL image suitable for Gemini input."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        return img.convert("RGB")


def call_gemini_model(
    model: genai.GenerativeModel,
    image_bytes: bytes,
    prompt: str,
) -> Optional[str]:
    """Invoke Gemini Vision model with prompt and image, returning text."""
    try:
        image = prepare_image_for_model(image_bytes)
        result = model.generate_content(
            [prompt, image],
            request_options={"timeout": REQUEST_TIMEOUT},
        )
        text = (result.text or "").strip()
        return text if text else None
    except Exception as exc:
        print(f"[오류] Gemini API 호출 실패: {exc}")
        return None


def ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_response(
    base_dir: pathlib.Path,
    call_id: int,
    parsed: Optional[dict],
    sanitized: Optional[str],
    raw: Optional[str],
) -> None:
    if parsed is not None:
        output_path = base_dir / f"{call_id}.json"
        output_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        output_path = base_dir / f"{call_id}.txt"
        content = sanitized or raw or ""
        output_path.write_text(content, encoding="utf-8")


def compare_problem_answers(
    base_dir: pathlib.Path,
    num_responses: int = 3,
) -> Dict[str, any]:
    """3개의 JSON 파일에서 problem_code와 answer가 다른 항목들을 비교 분석합니다."""
    
    # JSON 파일들 로드
    json_files = []
    for i in range(1, num_responses + 1):
        json_path = base_dir / f"{i}.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    json_files.append(data)
                    print(f"✅ {i}.json 로드 완료: {len(data)}개 문제")
            except Exception as e:
                print(f"❌ {i}.json 로드 실패: {e}")
                return {"error": f"JSON 파일 로드 실패: {e}"}
        else:
            print(f"❌ {i}.json 파일이 존재하지 않습니다.")
            return {"error": f"{i}.json 파일이 존재하지 않습니다."}
    
    if len(json_files) < 2:
        return {"error": "비교할 JSON 파일이 부족합니다."}
    
    # problem_code를 키로 하는 딕셔너리 생성
    problems_by_code = {}
    for file_idx, json_data in enumerate(json_files):
        for problem in json_data:
            code = problem.get("problem_code")
            if code not in problems_by_code:
                problems_by_code[code] = {}
            problems_by_code[code][f"response_{file_idx + 1}"] = {
                "answer": problem.get("answer"),
                "question_type": problem.get("question_type"),
                "unit_path": problem.get("unit_path"),
                "level": problem.get("level")
            }
    
    # 차이점 분석
    differences = []
    all_same = []
    missing_codes = []
    
    for code, responses in problems_by_code.items():
        if len(responses) < num_responses:
            missing_codes.append(code)
            continue
            
        # answer 비교
        answers = [resp["answer"] for resp in responses.values()]
        if len(set(answers)) > 1:  # 다른 답변이 있음
            differences.append({
                "problem_code": code,
                "responses": responses,
                "different_answers": list(set(answers))
            })
        else:
            all_same.append(code)
    
    # 결과 정리
    result = {
        "total_problems": len(problems_by_code),
        "same_answers": len(all_same),
        "different_answers": len(differences),
        "missing_problems": len(missing_codes),
        "differences": differences,
        "summary": {
            "same_problems": all_same,
            "missing_problems": missing_codes
        }
    }
    
    return result


def generate_difference_report(
    base_dir: pathlib.Path,
    comparison_result: Dict[str, any],
) -> None:
    """차이점 분석 결과를 상세 리포트로 저장합니다."""
    
    report_path = base_dir / "problem_differences_report.txt"
    
    report_lines = [
        "=== 문제별 답변 차이점 분석 리포트 ===",
        f"생성 시간: {json.dumps({'timestamp': __import__('datetime').datetime.now().isoformat()}, ensure_ascii=False, indent=2)}",
        "",
        "=== 요약 ===",
        f"총 문제 수: {comparison_result.get('total_problems', 0)}",
        f"동일한 답변: {comparison_result.get('same_answers', 0)}",
        f"다른 답변: {comparison_result.get('different_answers', 0)}",
        f"누락된 문제: {comparison_result.get('missing_problems', 0)}",
        "",
    ]
    
    # 차이점이 있는 문제들 상세 분석
    if comparison_result.get("differences"):
        report_lines.extend([
            "=== 답변이 다른 문제들 ===",
            ""
        ])
        
        for diff in comparison_result["differences"]:
            code = diff["problem_code"]
            report_lines.append(f"문제 {code}:")
            report_lines.append(f"  다른 답변들: {diff['different_answers']}")
            
            for resp_name, resp_data in diff["responses"].items():
                report_lines.append(f"  {resp_name}: {resp_data['answer']}")
            
            # 첫 번째 응답의 상세 정보
            first_resp = list(diff["responses"].values())[0]
            report_lines.append(f"  문제 유형: {first_resp['question_type']}")
            report_lines.append(f"  단원: {first_resp['unit_path']}")
            report_lines.append(f"  난이도: {first_resp['level']}")
            report_lines.append("")
    
    # 누락된 문제들
    if comparison_result.get("summary", {}).get("missing_problems"):
        report_lines.extend([
            "=== 누락된 문제들 ===",
            f"누락된 문제 코드: {comparison_result['summary']['missing_problems']}",
            ""
        ])
    
    # 동일한 답변을 가진 문제들 (처음 10개만 표시)
    same_problems = comparison_result.get("summary", {}).get("same_problems", [])
    if same_problems:
        report_lines.extend([
            "=== 동일한 답변을 가진 문제들 (샘플) ===",
            f"동일한 문제 수: {len(same_problems)}",
            f"샘플 문제 코드: {same_problems[:10]}",
            ""
        ])
    
    # 통계 정보
    report_lines.extend([
        "=== 통계 ===",
        f"일치율: {comparison_result.get('same_answers', 0) / max(comparison_result.get('total_problems', 1), 1) * 100:.1f}%",
        f"불일치율: {comparison_result.get('different_answers', 0) / max(comparison_result.get('total_problems', 1), 1) * 100:.1f}%",
    ])
    
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"📊 차이점 분석 리포트가 '{report_path}'에 저장되었습니다.")


def record_difference_log(
    base_dir: pathlib.Path,
    responses: List[Dict[str, Optional[str]]],
    num_calls: int,
) -> None:
    diff_log_path = base_dir / "differences.log"
    log_lines = [
        "Gemini 응답 불일치/실패 리포트",
        f"총 호출 수: {num_calls}",
        f"성공한 호출 수: {len(responses)}",
        "",
    ]

    for info in responses:
        call_id = info["call_id"]
        log_lines.append(f"[응답 {call_id}]")
        if info["parsed"] is not None:
            log_lines.append(
                json.dumps(info["parsed"], ensure_ascii=False, indent=2)
            )
        elif info["sanitized"]:
            log_lines.append(info["sanitized"])
        elif info["raw"]:
            log_lines.append(info["raw"])
        else:
            log_lines.append("(빈 응답)")
        log_lines.append("")

    unique_map: Dict[str, List[int]] = {}
    for info in responses:
        key = (
            json.dumps(info["parsed"], sort_keys=True, ensure_ascii=False)
            if info["parsed"] is not None
            else info["sanitized"]
            or info["raw"]
            or ""
        )
        unique_map.setdefault(key, []).append(info["call_id"])

    log_lines.append("=== 응답 그룹 ===")
    for content, call_ids in unique_map.items():
        log_lines.append(f"응답 동일 그룹: 호출 {call_ids}")
        log_lines.append(content)
        log_lines.append("")

    diff_log_path.write_text("\n".join(log_lines), encoding="utf-8")


# --- Main Workflow ---
def process_single_pdf(pdf_path: pathlib.Path, model: genai.GenerativeModel) -> None:
    """단일 PDF 파일을 처리합니다."""
    print(f"\n{'='*60}")
    print(f"📄 처리 중: {pdf_path.name}")
    print(f"{'='*60}")
    
    image_bytes = load_image_bytes(pdf_path)
    print(
        f"'{pdf_path.name}' 파일에 대해 Gemini API를 {NUM_CALL_ATTEMPTS}회 순차 호출합니다..."
    )

    responses: List[Dict[str, Optional[str]]] = []
    
    # 순차 처리로 변경 (병렬 → 순차)
    for call_id in range(1, NUM_CALL_ATTEMPTS + 1):
        try:
            print(f"[응답 {call_id}] Gemini API 호출 중...")
            result = call_gemini_model(model, image_bytes, PROMPT_TEXT)
            print(f"[응답 {call_id}] 성공")
            
            sanitized = sanitize_json_text(result) if result else None
            parsed = None
            if sanitized:
                try:
                    parsed = json.loads(sanitized)
                except json.JSONDecodeError:
                    parsed = None
            
            responses.append(
                {
                    "call_id": call_id,
                    "raw": result,
                    "sanitized": sanitized,
                    "parsed": parsed,
                }
            )
        except Exception as e:
            print(f"[응답 {call_id}] 실패: {e}")
            responses.append(
                {
                    "call_id": call_id,
                    "raw": None,
                    "sanitized": None,
                    "parsed": None,
                }
            )

    responses.sort(key=lambda item: item["call_id"])

    print("\n--- Gemini 응답 ---")
    for info in responses:
        call_id = info["call_id"]
        print(f"\n[응답 {call_id}]")
        if info["raw"]:
            print(info["raw"])
        else:
            print("(빈 응답)")

    if len(responses) < NUM_CALL_ATTEMPTS:
        print(
            f"\n⚠️ 요청 {NUM_CALL_ATTEMPTS}회 중 {len(responses)}회만 성공했습니다. "
            "불일치 여부 판단에 주의하세요."
        )

    ensure_dir(OUTPUT_DIR)
    target_output_dir = OUTPUT_DIR / pdf_path.stem
    ensure_dir(target_output_dir)

    for info in responses:
        save_response(
            target_output_dir,
            info["call_id"],
            info["parsed"],
            info["sanitized"],
            info["raw"],
        )

    all_calls_completed = len(responses) == NUM_CALL_ATTEMPTS
    all_parsed = all(
        info["parsed"] is not None for info in responses
    ) and all_calls_completed
    consistent = False
    representative = None
    if all_parsed:
        representative = responses[0]["parsed"]
        consistent = all(
            info["parsed"] == representative for info in responses[1:]
        )

    print("\n--- 비교 결과 ---")
    if consistent and representative is not None:
        print("✅ 모든 응답이 일치합니다. 신뢰도 높음.")
        merged_path = target_output_dir / "merged.json"
        merged_path.write_text(
            json.dumps(representative, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"결과를 '{merged_path}'에 저장했습니다.")
    else:
        print("❌ 응답이 일치하지 않거나 호출이 일부 실패했습니다. 수동 검토가 필요합니다.")
        record_difference_log(target_output_dir, responses, NUM_CALL_ATTEMPTS)
        print(f"상세 로그를 '{target_output_dir / 'differences.log'}'에 기록했습니다.")
        
        # 문제별 답변 차이점 분석
        print("\n=== 문제별 답변 차이점 분석 시작 ===")
        comparison_result = compare_problem_answers(target_output_dir, NUM_CALL_ATTEMPTS)
        
        if "error" not in comparison_result:
            print(f"📊 분석 완료:")
            print(f"  총 문제 수: {comparison_result['total_problems']}")
            print(f"  동일한 답변: {comparison_result['same_answers']}")
            print(f"  다른 답변: {comparison_result['different_answers']}")
            print(f"  누락된 문제: {comparison_result['missing_problems']}")
            
            # 상세 리포트 생성
            generate_difference_report(target_output_dir, comparison_result)
            
            # 차이점이 있는 문제들 출력 (처음 5개)
            if comparison_result['differences']:
                print(f"\n🔍 답변이 다른 문제들 (처음 5개):")
                for i, diff in enumerate(comparison_result['differences'][:5]):
                    code = diff['problem_code']
                    answers = diff['different_answers']
                    print(f"  {i+1}. 문제 {code}: {answers}")
        else:
            print(f"❌ 차이점 분석 실패: {comparison_result['error']}")


def main() -> None:
    """모든 PDF 파일을 순차적으로 처리합니다."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY를 .env 파일에 설정해주세요.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # Split 폴더의 모든 PDF 파일 가져오기
    split_dir = pathlib.Path("Split")
    if not split_dir.exists():
        raise FileNotFoundError("Split 폴더를 찾을 수 없습니다.")
    
    pdf_files = list(split_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError("Split 폴더에 PDF 파일이 없습니다.")
    
    # 파일명 순서로 정렬
    pdf_files.sort(key=lambda x: x.name)
    
    print(f"🚀 총 {len(pdf_files)}개 PDF 파일을 순차 처리합니다...")
    print(f"📁 처리할 파일들:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file.name}")
    
    # 각 PDF 파일 순차 처리
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"\n🔄 진행률: {i}/{len(pdf_files)}")
            process_single_pdf(pdf_file, model)
            print(f"✅ {pdf_file.name} 처리 완료!")
        except Exception as e:
            print(f"❌ {pdf_file.name} 처리 실패: {e}")
            continue
    
    print(f"\n🎉 모든 파일 처리 완료! ({len(pdf_files)}개 파일)")


def analyze_existing_results(target_dir: str = None) -> None:
    """기존에 생성된 JSON 파일들을 분석합니다."""
    if target_dir is None:
        target_dir = "Output/gemini/중1- 최종_page001"
    
    base_dir = pathlib.Path(target_dir)
    if not base_dir.exists():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {base_dir}")
        return
    
    print(f"📁 분석 대상 디렉토리: {base_dir}")
    print("=== 기존 JSON 파일들 분석 시작 ===")
    
    comparison_result = compare_problem_answers(base_dir, 3)
    
    if "error" not in comparison_result:
        print(f"📊 분석 완료:")
        print(f"  총 문제 수: {comparison_result['total_problems']}")
        print(f"  동일한 답변: {comparison_result['same_answers']}")
        print(f"  다른 답변: {comparison_result['different_answers']}")
        print(f"  누락된 문제: {comparison_result['missing_problems']}")
        
        # 상세 리포트 생성
        generate_difference_report(base_dir, comparison_result)
        
        # 차이점이 있는 문제들 출력 (처음 10개)
        if comparison_result['differences']:
            print(f"\n🔍 답변이 다른 문제들 (처음 10개):")
            for i, diff in enumerate(comparison_result['differences'][:10]):
                code = diff['problem_code']
                answers = diff['different_answers']
                print(f"  {i+1}. 문제 {code}: {answers}")
                
            if len(comparison_result['differences']) > 10:
                print(f"  ... 총 {len(comparison_result['differences'])}개 문제에서 차이 발견")
    else:
        print(f"❌ 차이점 분석 실패: {comparison_result['error']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        # 기존 결과 분석 모드
        target_dir = sys.argv[2] if len(sys.argv) > 2 else None
        analyze_existing_results(target_dir)
    else:
        # 기본 실행 모드 (Gemini API 호출)
        main()
