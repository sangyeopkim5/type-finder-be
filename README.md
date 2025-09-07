Manion-CAS

수학 문제 이미지를 Manim 애니메이션 코드로 자동 변환하는 AI 기반 시스템입니다.
OCR → GPT-5 → SVG 벡터화 → GeoCAS + CAS → 최종 Manim 코드까지 단일 파이프라인(/e2e) 으로 처리합니다.

Features

수학 문제 이미지 분석 및 OCR (텍스트/수식/라벨 자동 분류)

GPT-5 기반 코드 생성 (Manim Scene 초안 + GEO/CAS JOB 추출)

GeometryHint: Inkscape/Potrace/OpenCV 기반 도형 파라미터 추출

GeoCAS: SymPy Geometry 기반 좌표·각·접선 계산 (예각/둔각/호 방향까지 반영)

CAS: SymPy 기반 대수 변환 (단순화, 전개, 인수분해 등 – 화이트리스트 함수만 허용)

자동 Placeholder 치환 ([[GEO:*]], [[CAS:*]])

최종 Manim 코드 저장 및 실행 가이드 자동 생성

manion-cas/
├── apps/                                # 주요 앱 모듈
│   ├── cas/                             # CAS + GeoCAS 계산 모듈
│   │   ├── compute.py                   # run_cas(), run_geocas 구현
│   │   └── __init__.py
│   │
│   ├── codegen/                         # GPT-5 기반 코드 생성
│   │   ├── codegen.py                   # generate_manim()
│   │   ├── server.py                    # /codegen API → e2e 프록시
│   │   └── __init__.py
│   │
│   ├── render/                          # Placeholder 치환 로직
│   │   ├── fill.py                      # [[GEO:*]], [[CAS:*]] → 값 치환
│   │   └── __init__.py
│   │
│   └── router/                          # 문제 라우팅
│       ├── router.py                    # route_problem()
│       └── __init__.py
│
├── configs/                             # TOML 설정 파일 모음
│   ├── openai.toml                      # GPT-5 API key / model 설정
│   ├── render.toml                      # fill_placeholders 정책 (fail_build 등)
│   └── sympy.toml                       # SymPy 옵션
│
├── libs/                                # 공통 유틸
│   ├── layout.py                        # GeometryHint 추출 (OCR 라벨 → A,B,C,D 매핑)
│   ├── schemas.py                       # Pydantic 모델 정의 (ProblemDoc, CASJob 등)
│   ├── tokens.py                        # [[GEO:*]], [[CAS:*]] 토큰 파서
│   ├── io_utils.py                      # 파일 입출력, 경로 유틸
│   └── __init__.py
│
├── pipelines/                           # E2E 실행 스크립트
│   ├── e2e.py                           # 전체 파이프라인 실행
│   └── __init__.py
│
├── Probleminput/                        # 입력 문제 데이터 (이미지 + OCR JSON)
│   ├── 중3-1사다리꼴넓이.jpg
│   └── 중3-1사다리꼴넓이.json
│
├── ManimcodeOutput/                     # 최종 코드 출력 디렉토리
│   └── 중3-1사다리꼴넓이/
│       ├── 중3-1사다리꼴넓이.py         # 실행 가능한 Manim 코드
│       └── README.md                    # 실행 가이드
│
├── server.py                            # 메인 FastAPI 서버 (최상위)
├── requirements.txt                     # 의존성 목록
└── README.md                            # 문서



전체 파이프라인 로직

데이터 입력 (Input)

Probleminput/
├── 문제이름.jpg   # 수학 문제 이미지
└── 문제이름.json  # OCR 결과 및 문제 구조화 데이터


메인 파이프라인 (E2E)
server.py → /e2e

route_problem() : 문제 OCR 라우팅

extract_primitives_from_image() : SVG/라벨 기반 GeometryHint 추출
→ A,B,C,D 코너 라벨 매핑

generate_manim() : GPT-5로 코드 초안 + ---GEO-JOBS--- / ---CAS-JOBS--- 분리

run_geocas() : 좌표/각/접선 해석

run_cas() : 대수 계산

fill_placeholders() : [[GEO:]], [[CAS:]] 치환

최종 .py Manim 코드 출력

출력 구조

ManimcodeOutput/
└── 문제이름/
    ├── 문제이름.py    # 실행 가능한 코드
    └── README.md      # 실행 방법 안내


에러 처리

누락된 GEO/CAS → 즉시 실패 (fail_build)

라벨 미선언, 잘못된 토큰 패턴 → 422 에러

SVG 벡터화 실패 시 OpenCV 폴백

##실행 방법

가상환경 생성

cd manion-cas
python -m venv .venv


Windows PowerShell: .\.venv\Scripts\Activate.ps1

macOS/Linux: source .venv/bin/activate

의존성 설치

pip install -r requirements.txt


환경 변수 설정 (.env)

OPENAI_API_KEY=your_api_key_here


서버 실행

uvicorn server:app --reload --port 8000


API 문서: http://127.0.0.1:8000/docs

Health Check: http://127.0.0.1:8000/health

E2E 테스트

python -m pipelines.e2e "Probleminput/중3-1사다리꼴넓이/중3-1사다리꼴넓이.jpg" "Probleminput/중3-1사다리꼴넓이/중3-1사다리꼴넓이.json"


API Endpoints

POST /e2e
이미지 + OCR JSON → 최종 Manim 코드 반환 (권장 사용)

POST /codegen/generate
(호환용) GPT 기반 코드 초안 생성 → 내부적으로 /e2e 전체 실행을 프록시함

Development

테스트 실행

pytest


코드 포맷팅

black .
isort .

권장 시스템 스펙

Python 3.11+ (3.12 권장)

Windows 10/11, macOS 10.15+, Ubuntu 18.04+

RAM: 16GB 이상 권장

GPU (선택): NVIDIA CUDA → GeoCAS/OpenCV 성능 향상

Inkscape, Potrace 설치 시 SVG 벡터화 정확도 ↑

License

MIT License