py -3.11 -m venv venv

 .\venv\Scripts\activate

pip install -r requirements.txt

pip install --upgrade google-generativeai

python send_simple_prompt.py "오늘 날씨 요약해줘."
pip install -q -U google-genai