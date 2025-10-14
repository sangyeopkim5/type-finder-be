from dotenv import load_dotenv
import os, requests

# ✅ .env 경로를 명시적으로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
print(f"📁 로드할 .env 경로: {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path, override=True)

api_key = os.getenv("OPENAI_API_KEY")
print("🔑 불러온 원본 키:", repr(api_key))

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY를 .env에서 불러오지 못했습니다!")

# 문자열 정리
api_key = api_key.strip()
if api_key.startswith("OPENAI_API_KEY="):
    api_key = api_key.replace("OPENAI_API_KEY=", "").strip()

print("✅ 정제된 키:", repr(api_key))

# === 이하 동일 ===
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello, are you working?"}]
}

res = requests.post(url, headers=headers, json=data, timeout=30)
print("📡 상태코드:", res.status_code)
print("📦 응답:", res.text[:200])
