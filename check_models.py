import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("GOOGLE_API_KEY를 .env에 설정해주세요.")

genai.configure(api_key=api_key)

print("사용 가능한 모델 목록:")
for model in genai.list_models():
    methods = getattr(model, "supported_generation_methods", [])
    if methods and "generateContent" in methods:
        print(model.name)
