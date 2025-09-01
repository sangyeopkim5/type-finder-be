# Manion-CAS

수학 문제를 Manim 애니메이션으로 변환하는 AI 기반 시스템입니다.

## Features

- 수학 문제 이미지 분석 및 OCR
- GPT-5를 사용한 Manim 코드 생성
- CAS(Computer Algebra System) 계산 지원
- 자동 placeholder 치환 및 최종 코드 생성

## 전체 시스템 로직 흐름

### 1. 데이터 입력 (Input)
```
Probleminput/ 폴더의 문제 데이터
├── .jpg 파일: 수학 문제 이미지
└── .json 파일: OCR 결과 및 문제 구조화 데이터
```

### 2. 메인 파이프라인 (E2E Processing)
```
server.py → /e2e 엔드포인트
├── 1단계: route_problem() - 문제 분류 및 라우팅
├── 2단계: generate_manim() - GPT-5를 사용한 Manim 코드 생성
├── 3단계: run_cas() - CAS 계산 실행
└── 4단계: fill_placeholders() - 최종 코드 생성
```

### 3. 코드 생성 단계 (Code Generation)
```
apps/codegen/codegen.py
├── 이미지 처리: base64 인코딩 → GPT-5 Vision API 전송
├── 프롬프트 구성: base_text.md 또는 base_vision.md 템플릿 사용
├── GPT 응답 파싱: "---CAS-JOBS---" 구분자로 분리
└── CAS 작업 추출: [[CAS:id:expression]] 형식 파싱
```

### 4. CAS 계산 단계 (Computer Algebra System)
```
apps/cas/compute.py
├── 수식 파싱: parse_expr() + implicit_multiplication_application
├── 보안 검증: SAFE_FUNCS에 정의된 함수만 허용
├── 수학 계산: SymPy simplify() 함수 사용
└── 결과 변환: LaTeX 및 Python 문자열로 출력
```

### 5. 렌더링 단계 (Final Code Generation)
```
apps/render/fill.py
├── CAS 결과 매핑: id별로 계산 결과 연결
├── Placeholder 치환: [[CAS:id]] → 실제 계산값
└── 최종 Manim 코드 생성: 완성된 애니메이션 코드
```

### 6. 출력 (Output)
```
최종 결과: 완성된 Manim Python 코드
├── CAS 계산 완료된 수식
├── 애니메이션 시퀀스
└── 실행 가능한 Manim 스크립트
```

### 7. 에러 처리 및 로깅
```
각 단계별 예외 처리:
├── 422 Validation Error: 사용자 입력 오류
├── 500 Internal Server Error: 시스템 내부 오류
└── 상세한 오류 메시지와 스택 트레이스 제공
```

### 8. API 구조
```
FastAPI 기반 모듈화된 구조:
├── /e2e: 전체 파이프라인 실행
├── /codegen/generate: 코드 생성만
├── /cas/compute: CAS 계산만
└── /render/fill: 렌더링만
```

### 9. 데이터 흐름 요약
```
Input (이미지+JSON) 
→ GPT-5 Vision API (코드 생성)
→ CAS 계산 (SymPy)
→ Placeholder 치환
→ Output (완성된 Manim 코드)
```

### 10. 저장 및 출력 (구현 완료)
```
자동 저장 시스템 구현 완료:
├── ManimcodeOutput/ 폴더에 문제별 폴더 생성
├── 문제 이름과 동일한 폴더명 사용
├── 실행 가능한 Manim 코드: {문제명}.py
├── 실행 방법 안내: README.md
└── 바로 실행 가능한 Python 파일

저장 구조:
ManimcodeOutput/
├── 중1sample/
│   ├── 중1sample.py            # 실행 가능한 Manim 코드
│   └── README.md               # 실행 방법 안내
├── 중2sample/
│   ├── 중2sample.py
│   └── README.md
└── ...

실행 방법:
manim 중1sample.py -pql
```

## Layout

```
manion-cas/
├── apps/                          # 애플리케이션 모듈
│   ├── cas/                      # CAS 계산 모듈
│   │   ├── compute.py            # SymPy 기반 수학 계산
│   │   ├── server.py             # CAS API 서버
│   │   └── tests/                # CAS 테스트
│   ├── codegen/                  # 코드 생성 모듈
│   │   ├── codegen.py            # GPT 기반 Manim 코드 생성
│   │   ├── server.py             # 코드생성 API 서버
│   │   ├── prompt_templates/     # GPT 프롬프트 템플릿
│   │   └── tests/                # 코드생성 테스트
│   ├── render/                   # 렌더링 모듈
│   │   ├── fill.py               # Placeholder 치환
│   │   ├── server.py             # 렌더링 API 서버
│   │   └── tests/                # 렌더링 테스트
│   └── router/                   # 라우팅 모듈
│       ├── router.py             # 문제 분류 및 라우팅
│       ├── server.py             # 라우팅 API 서버
│       └── tests/                # 라우팅 테스트
├── configs/                       # 설정 파일
│   ├── openai.toml               # OpenAI API 설정
│   ├── render.toml               # 렌더링 설정
│   └── sympy.toml                # SymPy 설정
├── libs/                          # 공통 라이브러리
│   ├── __init__.py
│   ├── io_utils.py               # 입출력 유틸리티
│   ├── layout.py                 # 레이아웃 분석
│   ├── schemas.py                # 데이터 스키마
│   └── tokens.py                 # OpenAI 클라이언트
├── pipelines/                     # 파이프라인
│   ├── e2e.py                    # End-to-End 테스트
│   └── tests/                    # 파이프라인 테스트
├── Probleminput/                  # 문제 입력 데이터
│   ├── 중1sample/                # 중1 샘플 문제
│   ├── 중2sample/                # 중2 샘플 문제
│   ├── 중3-1객관식/              # 중3 객관식 문제
│   ├── 중3-1그래프의 모양/        # 중3 그래프 문제
│   ├── 중3-1그래프추론/           # 중3 그래프 추론
│   ├── 중3-1기호문제/            # 중3 기호 문제
│   ├── 중3-1사다리꼴넓이/         # 중3 도형 문제
│   └── 중3-1함숫값계산/           # 중3 함수 문제ㅎㅎ
├── ManimcodeOutput/               # 생성된 Manim 코드 출력
│   ├── 중1sample/                # 중1 샘플 코드
│   │   ├── 중1sample.py         # 실행 가능한 Manim 코드
│   │   └── README.md            # 실행 방법 안내
│   └── ...                      # 기타 생성된 코드
├── server.py                      # 메인 FastAPI 서버
├── requirements.txt               # Python 의존성
├── system_prompt.txt              # 시스템 프롬프트
└── README.md                      # 프로젝트 문서
```

## 실행법

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성

cd manion-cas

python -m venv .venv

# 가상환경 활성화 (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 가상환경 활성화 (Windows CMD)
.venv\Scripts\activate.bat

# 가상환경 활성화 (Linux/Mac)
source .venv/bin/activate
```

### 2. 의존성 설치

```bash
# 가상환경이 활성화된 상태에서
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정:

```bash
# .env 파일 생성
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 4. 서버 실행

```bash
# 개발 모드로 서버 실행 (코드 변경 시 자동 재시작)
uvicorn server:app --reload --port 8000

# 또는 기본 포트로 실행
uvicorn server:app --reload
```

### 5. 서버 접속 확인

- **API 문서**: http://127.0.0.1:8000/docs
- **서버 상태**: http://127.0.0.1:8000/
- **Health Check**: http://127.0.0.1:8000/health

### 6. 새로운 터미널에서 ProblemInput 테스트

```bash
# 새 터미널 열기 (가상환경 활성화 필요)
cd manion-cas

.venv\Scripts\Activate.ps1  # Windows PowerShell
# 또는
.venv\Scripts\activate.bat  # Windows CMD

# E2E 파이프라인 테스트
python -m pipelines.e2e "Probleminput/중1sample/중1sample.jpg" "Probleminput/중1sample/중1sample.json"

# 다른 문제 테스트
python -m pipelines.e2e "Probleminput/중2sample/중2sample.jpg" "Probleminput/중2sample/중2sample.json"
```

## API Endpoints

- **POST /e2e**: End-to-End 처리 (이미지 → Manim 코드)
- **POST /codegen/generate**: 코드 생성만
- **POST /cas/compute**: CAS 계산만
- **POST /render/fill**: Placeholder 치환만

## Troubleshooting

### 일반적인 문제들

1. **포트 충돌**: 다른 포트 사용
   ```bash
   uvicorn server:app --reload --port 8001
   ```

2. **가상환경 비활성화**: 터미널 재시작 후 재활성화

3. **의존성 문제**: 가상환경 삭제 후 재생성
   ```bash
   rmdir /s .venv
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

### 서버 로그 확인

서버 실행 시 터미널에서 실시간 로그를 확인할 수 있습니다:
- 정상 시작: "Application startup complete"
- 오류 발생: 상세한 오류 메시지와 스택 트레이스

## Development

### 테스트 실행

```bash
# 전체 테스트 실행
python -m pytest

# 특정 모듈 테스트
python -m pytest apps/codegen/tests/
python -m pytest apps/cas/tests/
```

### 코드 포맷팅

```bash
# Black으로 코드 포맷팅
black .

# isort로 import 정렬
isort .
```

## 문제해결법.

로그에 나타난 문제를 연동된 codex에 그대로 붙혀넣고 원인파악-> Cursor내부에서 수정요청.하면 간단한 것은 해결.

## 권장 시스템 스펙

### 필수 요구사항
- **Python**: 3.11 이상 (3.11, 3.12, 3.13)
- **운영체제**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **메모리**: 최소 8GB RAM (권장 16GB 이상)
- **저장공간**: 최소 2GB 여유 공간

### 권장 사양
- **Python**: 3.12 (최신 안정 버전)
- **메모리**: 16GB RAM 이상
- **CPU**: Intel i5/AMD Ryzen 5 이상 (멀티코어)
- **네트워크**: 안정적인 인터넷 연결 (OpenAI API 호출용)

### Python 버전별 지원
- **Python 3.11**: ✅ 완전 지원 (tomllib 내장)
- **Python 3.12**: ✅ 완전 지원 (최신 기능)
- **Python 3.13**: ✅ 완전 지원 (최신 기능)
- **Python 3.10 이하**: ❌ 지원하지 않음 (tomllib 미지원)

### 추가 권장사항
- **가상환경**: Python venv 또는 conda 사용
- **에디터**: VS Code, PyCharm, Cursor 등
- **터미널**: PowerShell (Windows), Terminal (macOS), Bash (Linux)

## License

이 프로젝트는 MIT 라이선스 하에 배포됩니다.