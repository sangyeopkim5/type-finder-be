🎯 전체 목적

OCR로 얻은 수학 문제 → 결정적 JSON 변환

문제문 재구성

라우팅 결정(JSON-only vs JSON+Image)

CAS 작업/목표 정의

**여러 Tree-of-Thought 가지(branch)**와 각 단계(step)의 SymPy 실행 코드 (result = ...) 포함

비용 최소화

기본: 텍스트 전용(gpt-4o-mini)

예외: Router가 필요하다고 판정한 경우에만 **멀티모달(gpt-4o)**로 이미지+텍스트 전달

검증 가능성

GPT가 생성한 SymPy 코드 → 로컬 실행 → 실제 수학 계산 결과 확인

📂 파일 구조 및 역할
manion-cas-compiler/
│
├── prompts/
│   └── system_prompt.txt   # GPT에게 전달할 시스템 프롬프트
│
├── src/
│   ├── __init__.py         # 패키지 초기화, system_prompt 로더
│   ├── router.py           # Router: 이미지 필요 여부 판단
│   ├── client_gpt.py       # GPT 호출 래퍼 (4o-mini 기본, 필요시 4o)
│   ├── compiler.py         # 전체 오케스트레이션 (Router + GPT 호출 + 결과 저장)
│   └── executor.py         # GPT가 생성한 SymPy 코드 실행기
│
├── Probleminput/           # 입력 문제들 (OCR JSON + 이미지 + MD)
│   ├── ex-001.json
│   ├── ex-001.jpg
│   └── ex-001.md
│
└── output_results/         # GPT 결과(JSON) 및 실행 결과
    └── ex-001_result.json

⚙️ 주요 함수별 역할
src/router.py

함수: infer_routing(segments_json)

OCR 세그먼트 분석 → 이미지 필요 여부 판정

규칙 기반 점수화:

Picture, Table, Caption 카테고리 → 가중치 ↑

텍스트에 “그림, 도형, 그래프, 좌표, ∠ …” 등 → 가중치 ↑

“그림 없이” → 가중치 ↓

출력:

{"need_image": true/false, "confidence": 0.0~1.0, "reasons": ["string"]}

src/client_gpt.py

함수: call_manion_model(segments_json, problem_meta, need_image=...)

Router 판정에 따라 모델 전환:

need_image=False → gpt-4o-mini (텍스트-only)

need_image=True → gpt-4o (이미지+텍스트 멀티모달)

항상 response_format={"type":"json_object"} → JSON만 반환

실패 시 원본 응답 last_raw_response.txt에 저장

src/compiler.py

클래스: ManionCASCompiler

주요 메서드: compile(segments_json, problem_meta)

동작 순서:

infer_routing()으로 라우팅 결정

필요 시 Probleminput/에서 이미지 자동 검색 후 problem_meta에 추가

call_manion_model() 호출 → GPT 실행

결과 JSON을 output_results/{problem_id}_result.json에 저장

src/executor.py

함수: run_sympy_steps(result_json)

GPT가 반환한 branches/steps 안의 sympy_code를 순차 실행

실행 결과를 콘솔 출력(또는 DB에 저장 가능)

🔄 전체 데이터 흐름
[Probleminput/*.json]  ← OCR 세그먼트
        │
        ▼
ManionCASCompiler.compile()
    1) infer_routing() → 이미지 필요 여부 결정
    2) 이미지 필요 시 Probleminput/에서 .jpg 검색
    3) call_manion_model()
         ├─ gpt-4o-mini (기본)
         └─ gpt-4o (이미지 필요 시)
    4) GPT 출력 JSON 저장 → output_results/
        │
        ▼
[SymPy 실행] run_sympy_steps()