#!/usr/bin/env python3
"""
Manion CAS Compiler 실행 예제
기존 문제 파일을 사용하여 컴파일러를 테스트합니다.
"""

import json
import os
from pathlib import Path
from src.compiler import ManionCASCompiler

def main():
    print("🚀 Manion CAS Compiler 실행 중...")
    
    # 환경 변수 확인
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 OPENAI_API_KEY=your_key_here를 추가하세요.")
        return
    
    # 컴파일러 인스턴스 생성
    compiler = ManionCASCompiler()
    
    # 테스트할 문제 선택 (중1sample 사용)
    problem_dir = "Probleminput/중3-1그래프의 모양"
    problem_id = "중3-1그래프의 모양"
    
    # JSON 파일 읽기
    json_path = Path(problem_dir) / f"{problem_id}.json"
    if not json_path.exists():
        print(f"❌ 문제 파일을 찾을 수 없습니다: {json_path}")
        return
    
    print(f"📖 문제 파일 읽는 중: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        segments_json = json.load(f)
    
    print(f"📊 OCR 세그먼트 수: {len(segments_json)}")
    
    # 문제 메타데이터 설정
    problem_meta = {
        "problem_id": problem_id,
        "subject": "중학교 1학년",
        "topic": "식의 계산",
        "description": "다항식의 덧셈과 뺄셈"
    }
    
    print(f"🎯 문제 ID: {problem_id}")
    print(f"📚 주제: {problem_meta['topic']}")
    
    try:
        # 컴파일 실행
        print("\n🔄 컴파일 실행 중...")
        result = compiler.compile(segments_json, problem_meta)
        
        print("✅ 컴파일 완료!")
        print(f"📁 결과 저장 위치: output_results/{problem_id}_result.json")
        
        # 결과 요약 출력
        if "branches" in result:
            print(f"🌳 생성된 브랜치 수: {len(result['branches'])}")
            for i, branch in enumerate(result['branches']):
                if "steps" in branch:
                    print(f"   브랜치 {i+1}: {len(branch['steps'])} 단계")
        
        # SymPy 실행 (선택사항)
        print("\n🧮 SymPy 코드 실행 중...")
        from src.executor import run_sympy_steps
        run_sympy_steps(result)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
