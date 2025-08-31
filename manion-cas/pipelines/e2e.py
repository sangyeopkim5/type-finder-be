import json
import sys
import httpx
from libs.schemas import ProblemDoc

if __name__ == "__main__":
    img = sys.argv[1]
    js = sys.argv[2]
    items = json.load(open(js, "r", encoding="utf-8"))
    data = ProblemDoc(items=items, image_path=img)
    with httpx.Client(timeout=30) as client:
        r = client.post("http://localhost:8000/e2e", json=data.model_dump())
        if r.status_code == 200:
            result = r.json()
            manim_code = result["manim_code"]
            
            # 코드 블록 마커는 이미 codegen.py에서 제거됨
            manim_code = manim_code.strip()
            
            print(manim_code)
        else:
            print(f"Error {r.status_code}: {r.text}")
