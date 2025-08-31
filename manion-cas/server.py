from fastapi import FastAPI, HTTPException
from libs.schemas import ProblemDoc, CASJob
from apps.router.server import router as router_router
from apps.codegen.server import router as codegen_router
from apps.cas.server import router as cas_router
from apps.render.server import router as render_router
from apps.codegen.codegen import generate_manim
from apps.cas.compute import run_cas
from apps.render.fill import fill_placeholders
from apps.router.router import route_problem
import os
import json
from datetime import datetime
from pathlib import Path


app = FastAPI(title="Manion-CAS")

app.include_router(router_router)
app.include_router(codegen_router)
app.include_router(cas_router)
app.include_router(render_router)


@app.post("/e2e")
def e2e(doc: ProblemDoc):
    # ManimcodeOutput 폴더 생성
    output_dir = Path("ManimcodeOutput")
    output_dir.mkdir(exist_ok=True)
    
    # 문제 이름 추출 (이미지 경로에서)
    problem_name = Path(doc.image_path).stem if doc.image_path else "unknown"
    problem_dir = output_dir / problem_name
    problem_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Route problem
        try:
            route_problem(doc)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Problem routing failed: {str(e)}")
        
        # Step 2: Generate manim code
        try:
            cg = generate_manim(doc)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Code generation failed: {str(e)}")
        
        # Step 3: Create CAS jobs
        try:
            jobs = [CASJob(**j) for j in cg.cas_jobs]
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"CAS job creation failed: {str(e)}")
        
        # Step 4: Run CAS computation
        try:
            cas_res = run_cas(jobs)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"CAS computation failed: {str(e)}")
        
        # Step 5: Fill placeholders
        try:
            final = fill_placeholders(cg.manim_code_draft, cas_res)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Placeholder filling failed: {str(e)}")
        
        # Manim 코드를 파일로 저장
        try:
            manim_file = problem_dir / f"{problem_name}.py"
            
            # 코드 블록 마커는 이미 codegen.py에서 제거됨
            manim_code_clean = final.manim_code_final.strip()
            
            with open(manim_file, "w", encoding="utf-8") as f:
                f.write(manim_code_clean)
            
            # 실행 방법 안내 파일 생성
            readme_file = problem_dir / "README.md"
            with open(readme_file, "w", encoding="utf-8") as f:
                f.write(f"# {problem_name} Manim Code\n\n")
                f.write(f"## 실행 방법\n\n")
                f.write(f"1. Manim 설치: `pip install manim`\n")
                f.write(f"2. 코드 실행: `manim {problem_name}.py -pql`\n")
                f.write(f"   - `-p`: 완료 후 자동 재생\n")
                f.write(f"   - `-q`: 품질 설정 (l=low, m=medium, h=high)\n")
                f.write(f"   - `-l`: 라이브 프리뷰\n\n")
                f.write(f"## 파일 설명\n\n")
                f.write(f"- `{problem_name}.py`: 실행 가능한 Manim 코드\n")
                f.write(f"- `README.md`: 이 파일 (실행 방법 안내)\n\n")
                f.write(f"## 생성 시간\n")
                f.write(f"- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
        except Exception as e:
            print(f"Warning: Failed to save output files: {e}")
        
        return {"manim_code": final.manim_code_final}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        error_detail = f"Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/")
def read_root():
    return {"message": "Manion-CAS API Server"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

