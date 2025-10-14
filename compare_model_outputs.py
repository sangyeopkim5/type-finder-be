import argparse
import json
import pathlib
from typing import Dict, List, Optional, Tuple


CALL_IDS = (1, 2, 3)


def load_json_list(path: pathlib.Path) -> Tuple[Optional[List[dict]], Optional[str]]:
    """Load a JSON list from disk, returning (data, error_message)."""
    if not path.exists():
        return None, "파일을 찾을 수 없습니다."
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"JSON 디코딩 실패: {exc}"
    if not isinstance(data, list):
        return None, "최상위 구조가 리스트가 아닙니다."
    return data, None


def index_entries(entries: List[dict]) -> Tuple[Dict[str, List[dict]], List[str]]:
    """Index entries by problem_code and collect structural issues."""
    mapping: Dict[str, List[dict]] = {}
    issues: List[str] = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(f"{idx + 1}번째 항목이 객체(dict)가 아닙니다.")
            continue
        code = entry.get("problem_code")
        if not code:
            issues.append(f"{idx + 1}번째 항목에 problem_code가 없습니다.")
            continue
        code_str = str(code)
        mapping.setdefault(code_str, []).append(entry)
    return mapping, issues


def format_value(value) -> str:
    """Render a value for human-readable comparison logs."""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def compare_attempt(
    call_id: int,
    gem_path: pathlib.Path,
    gpt_path: pathlib.Path,
) -> Tuple[bool, List[str]]:
    """Compare a single call's outputs and return (is_match, detail_logs)."""
    details: List[str] = []
    gem_data, gem_err = load_json_list(gem_path)
    gpt_data, gpt_err = load_json_list(gpt_path)

    if gem_err:
        details.append(f"Gemini {call_id}.json: {gem_err}")
    if gpt_err:
        details.append(f"GPT {call_id}.json: {gpt_err}")

    if gem_data is None or gpt_data is None:
        return False, details

    match = True

    if len(gem_data) != len(gpt_data):
        details.append(
            f"총 항목 수 불일치 (Gemini {len(gem_data)}개 vs GPT {len(gpt_data)}개)."
        )
        match = False

    gem_map, gem_issues = index_entries(gem_data)
    gpt_map, gpt_issues = index_entries(gpt_data)

    if gem_issues:
        match = False
        details.extend(f"Gemini 데이터 경고: {msg}" for msg in gem_issues)
    if gpt_issues:
        match = False
        details.extend(f"GPT 데이터 경고: {msg}" for msg in gpt_issues)

    all_codes = sorted(set(gem_map) | set(gpt_map))
    for code in all_codes:
        gem_list = gem_map.get(code, [])
        gpt_list = gpt_map.get(code, [])

        if not gem_list:
            details.append(f"문제 {code}: Gemini 결과 누락.")
            match = False
            continue
        if not gpt_list:
            details.append(f"문제 {code}: GPT 결과 누락.")
            match = False
            continue

        if len(gem_list) != 1 or len(gpt_list) != 1:
            details.append(
                f"문제 {code}: 중복 항목 존재 (Gemini {len(gem_list)}개, GPT {len(gpt_list)}개)."
            )
            match = False

        gem_entry = gem_list[0]
        gpt_entry = gpt_list[0]
        diff_keys = [
            key
            for key in sorted(set(gem_entry.keys()) | set(gpt_entry.keys()))
            if gem_entry.get(key) != gpt_entry.get(key)
        ]
        if diff_keys:
            diff_desc = ", ".join(
                f"{key} → Gemini={format_value(gem_entry.get(key))}, GPT={format_value(gpt_entry.get(key))}"
                for key in diff_keys
            )
            details.append(f"문제 {code}: {diff_desc}")
            match = False

    return match, details


def collect_subdirectories(root: pathlib.Path) -> List[str]:
    """Return sorted list of subdirectory names under root."""
    if not root.exists():
        return []
    return sorted(
        entry.name for entry in root.iterdir() if entry.is_dir()
    )


def ensure_dir(path: pathlib.Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def compare_directories(
    gem_root: pathlib.Path,
    gpt_root: pathlib.Path,
) -> Tuple[bool, List[str]]:
    """Compare all common subdirectories and collect report lines."""
    gem_dirs = collect_subdirectories(gem_root)
    gpt_dirs = collect_subdirectories(gpt_root)
    common_dirs = sorted(set(gem_dirs) & set(gpt_dirs))

    overall_match = True
    logs: List[str] = []

    if not common_dirs:
        logs.append("⚠️ 공통 디렉터리가 없습니다. 입력 경로를 확인해주세요.")
        return False, logs

    for name in common_dirs:
        logs.append(f"=== {name} ===")
        dataset_match = True

        for call_id in CALL_IDS:
            gem_path = gem_root / name / f"{call_id}.json"
            gpt_path = gpt_root / name / f"{call_id}.json"

            call_match, details = compare_attempt(call_id, gem_path, gpt_path)
            if call_match:
                logs.append(f"[{call_id}.json] ✅ 모든 항목 일치")
            else:
                dataset_match = False
                overall_match = False
                logs.append(f"[{call_id}.json] ❌ 불일치 발견")
                logs.extend(f"    - {line}" for line in details)

        if dataset_match:
            logs.append("→ ✅ 디렉터리 전체 일치")
        else:
            logs.append("→ ❌ 디렉터리에서 불일치 발견")
        logs.append("")

    missing_for_gpt = sorted(set(gem_dirs) - set(gpt_dirs))
    missing_for_gemini = sorted(set(gpt_dirs) - set(gem_dirs))

    if missing_for_gpt:
        overall_match = False
        logs.append(
            "GPT에 존재하지 않는 Gemini 디렉터리: " + ", ".join(missing_for_gpt)
        )
    if missing_for_gemini:
        overall_match = False
        logs.append(
            "Gemini에 존재하지 않는 GPT 디렉터리: " + ", ".join(missing_for_gemini)
        )

    return overall_match, logs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gemini와 GPT 응답 JSON(1~3회차)을 비교합니다."
    )
    parser.add_argument(
        "--gemini",
        type=pathlib.Path,
        default=pathlib.Path("Output/gemini"),
        help="Gemini 출력 디렉터리 (기본값: Output/gemini)",
    )
    parser.add_argument(
        "--gpt",
        type=pathlib.Path,
        default=pathlib.Path("Output/gpt"),
        help="GPT 출력 디렉터리 (기본값: Output/gpt)",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("Output/comparison"),
        help="비교 로그를 저장할 디렉터리 (기본값: Output/comparison)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gem_root = args.gemini
    gpt_root = args.gpt

    if not gem_root.exists():
        raise FileNotFoundError(f"Gemini 출력 경로를 찾을 수 없습니다: {gem_root}")
    if not gpt_root.exists():
        raise FileNotFoundError(f"GPT 출력 경로를 찾을 수 없습니다: {gpt_root}")

    overall_match, logs = compare_directories(gem_root, gpt_root)

    ensure_dir(args.output)
    log_path = args.output / "comparison_log.txt"
    log_path.write_text("\n".join(logs), encoding="utf-8")

    print("\n".join(logs))
    print()
    if overall_match:
        print("✅ 모든 비교 결과가 일치합니다.")
    else:
        print("❌ 불일치가 발견되었습니다. 상세 로그:", log_path)


if __name__ == "__main__":
    main()

