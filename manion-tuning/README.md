# README.md — YouTube 스크립트 기반 스토리보드 튜닝 세트

## 1) 증강 스크립트(텍스트 원문 확장): `src/augment_scripts.py`

**목적**: 유튜브 스크립트 원문(약 20개)을 문장 단위 분할/삭제/순서섞기/오타 삽입/길이 절단 등 **룰 기반 노이즈**로 증강해 `data/raw_aug/`에 저장. 이 스텝만으로 수백\~수천 샘플까지 확장 가능. &#x20;

**핵심 코드 조각(문서 수록 내용):**

```python
import os, glob, random, re
from pathlib import Path
random.seed(42)
SRC = "data/raw"
DST = "data/raw_aug"
os.makedirs(DST, exist_ok=True)

def sent_split(t):
    # 아주 단순 분할(영/한 섞여도 대충 동작)
    return re.split(r'(?<=[.!?])\s+', t.strip())

def inject_typos(text, p=0.01):
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < p and chars[i].isalpha():
            chars[i] = chars[i].swapcase()
    return "".join(chars)

def drop_sentences(sents, drop_p=0.05):
    return [s for s in sents if random.random() > drop_p]

def swap_adjacent(sents, swap_p=0.05):
    sents = sents[:]
    i = 0
    while i < len(sents)-1:
        if random.random() < swap_p:
            sents[i], sents[i+1] = sents[i+1], sents[i]; i += 2
        else:
            i += 1
    return sents

def truncate(text, min_len=800):
    if len(text) <= min_len: return text
    cut = random.randint(min_len, int(len(text)*0.95))
    return text[:cut]

def augment_once(text):
    sents = sent_split(text)
    sents = drop_sentences(sents, 0.03)
    sents = swap_adjacent(sents, 0.07)
    t = " ".join(sents)
    t = truncate(t, 600)
    t = inject_typos(t, 0.003)
    return t
```

&#x20;&#x20;

> 운영 메모: “AUG\_PER=9 → 원본+9=10배” 루틴이 지침으로 주어져 있어, 원문이 20개면 최종 200개 규모가 된다(예: 21개면 189개 추가 생성 로그).&#x20;

---

## 2) 라벨 증강(스토리보드 JSON 재작성): `src/augment_labels.py`

**목적**: 사람이 만든 스토리보드 라벨(`data/label/*.json`)을 **모델로 “의미 보존+표현 다양화”** 하여 여러 개(`__aug1..__aug9.json`)로 불려 `data/label_aug/`에 저장. **AUG\_PER=9** 기준으로 라벨당 9개 생성.&#x20;

**핵심 로직(문서 수록 내용):**

* 각 라벨 JSON을 읽어 **LLM이 manim\_preset 분포/내레이션을 살짝 바꾼 JSON**을 생성. 결과를 `__aug{i}.json`으로 저장, 총합을 요약 출력. &#x20;

```python
# (요약된 핵심 흐름)
import os, json, glob, re, time

SRC_DIR = "data/label"
OUT_DIR = "data/label_aug"
AUG_PER = 9  # 운영 지침

def augment_one(sb):
    # 문서의 OpenAI 재작성 스펙을 따른 함수화 (schema 강제, preset 다양화)
    # SYSTEM/User 프롬프트/force_json 로직은 문서 수록 코드를 사용
    ...

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.json")))
made = 0
for fp in files:
    name = os.path.basename(fp)
    if "__aug" in name: 
        continue
    sb = json.load(open(fp, encoding="utf-8"))
    for i in range(1, AUG_PER+1):
        aug = augment_one(sb)
        out_path = os.path.join(OUT_DIR, f"{os.path.splitext(name)[0]}__aug{i}.json")
        json.dump(aug, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        made += 1
        time.sleep(0.2)  # API 속도 제한 보호
print(f"✅ augmented: {made} files -> {OUT_DIR}")
```

&#x20;

> 숫자 근거: “원본 21개 × 9 = 189개”라는 실행 예가 대화에 기록됨.&#x20;

---

## 3) 오토라벨(원문 → 스토리보드 라벨 자동 생성): `src/auto_label.py`

**목적**: **골드라벨이 없는 원문**에 대해 모델로 **스토리보드 라벨을 자동 생성**, 스키마 검증 통과분만 채택해 `data/label_auto/`에 저장. 실행 명령은 `python src/auto_label.py`.&#x20;

**문서 수록된 실행/로그 근거:**

* “스키마 검증 통과분만 채택”, “✅ 오토라벨 생성: N개 → OUT\_DIR” 출력, `main()` 엔트리. &#x20;

> 운영 루틴: **골드(5\~10개) + 대량 오토라벨** 전략으로 train/val을 구성해 성능 상승을 빠르게 달성. 원문은 `data/raw/2.txt` \~ `21.txt`에서 먼저 5\~10개 골드화 지시 있음.&#x20;

---

## 4) 학습 세트 빌드(JSONL): `src/build_jsonl.py`

**목적**: `data/label/*.json`(골드) + `data/label_auto/*.json`(오토)를 매칭되는 원문(`data/raw/` 및 `data/raw_aug/`)과 **페어링**해, OpenAI 파인튜닝용 **`train.jsonl` / `val.jsonl`** 생성. &#x20;

**문서 수록 코드(요지):**

```python
import sys, os, glob, json
from jsonschema import validate
from src.schema import STORYBOARD_SCHEMA

SYSTEM = "너의 임무는 유튜브 수학 스크립트를 Manim 스토리보드(JSON)로 구조화하는 것이다. 반드시 지정 스키마를 준수하라."
USER_TMPL = "<SCRIPT>\n{script}\n</SCRIPT>\n요구사항: 4~6개 씬, 씬당 2~4샷, manim_preset 필수, tone=멘토, pace=중간"

def dump(fp, script_path, label_path):
    script = open(script_path,encoding="utf-8").read()
    gold = json.load(open(label_path,encoding="utf-8"))
    validate(instance=gold, schema=STORYBOARD_SCHEMA)
    sample = {
      "messages":[
        {"role":"system","content": SYSTEM},
        {"role":"user","content": USER_TMPL.format(script=script)},
        {"role":"assistant","content": json.dumps(gold, ensure_ascii=False)}
      ]
    }
    fp.write(json.dumps(sample, ensure_ascii=False)+"\n")

def main():
    os.makedirs("data/build", exist_ok=True)
    labels = sorted(glob.glob("data/label/*.json")) + sorted(glob.glob("data/label_auto/*.json"))
    assert labels, "라벨 JSON이 없습니다."
    # filename stem 기반 raw/raw_aug 매칭
    pairs = []
    for lab in labels:
        name = os.path.splitext(os.path.basename(lab))[0]
        for raw_dir in ("data/raw","data/raw_aug"):
            rawp = f"{raw_dir}/{name}.txt"
            if os.path.exists(rawp):
                pairs.append((rawp, lab)); break
```

&#x20;&#x20;

**파일 생성부(문서 수록):**

```python
with open("data/build/train.jsonl","w",encoding="utf-8") as ftrain, \
     open("data/build/val.jsonl","w",encoding="utf-8") as fval:
    for lab in train_labels:
        name = os.path.splitext(os.path.basename(lab))[0]
        rawp = f"data/raw/{name}.txt"
        if os.path.exists(rawp):
            dump(ftrain, rawp, lab)
    for lab in val_labels:
        name = os.path.splitext(os.path.basename(lab))[0]
        rawp = f"data/raw/{name}.txt"
        if os.path.exists(rawp):
            dump(fval, rawp, lab)
print("✅ JSONL 생성 완료: data/build/train.jsonl, val.jsonl")
```

&#x20;

---

## 5) 파인튜닝 실행: `src/ft_openai.py`

**목적**: `train.jsonl`/`val.jsonl` 업로드 후 Fine-tune 잡 생성, 완료 시 모델 ID 획득.&#x20;

**문서 수록 코드(완성형):**

```python
from openai import OpenAI
client = OpenAI()

def main():
    tr = client.files.create(file=open("data/build/train.jsonl","rb"), purpose="fine-tune")
    va = client.files.create(file=open("data/build/val.jsonl","rb"),   purpose="fine-tune")
    job = client.fine_tuning.jobs.create(
        training_file=tr.id,
        validation_file=va.id,
        model="gpt-4o-mini"   # 사용 가능한 SFT 대상 중 하나
    )
    print("Fine-tune job:", job.id)

if __name__=="__main__":
    main()
```

&#x20;&#x20;

---

## 6) 튜닝 모델 추론(스토리보드 생성): `src/infer_openai.py` / `src/infer_ft.py`

**목적**: **튜닝 완료 모델 ID**와 **원문 스크립트**를 받아, **스토리텔링이 강화된 JSON 스토리보드**를 생성. \*\*JSON 스키마 강제(response\_format/json\_schema)\*\*로 정확도를 보강. &#x20;

**문서 수록 코드(요지):**

```python
import json, sys
from openai import OpenAI
from src.schema import STORYBOARD_SCHEMA
client = OpenAI()

def infer(ft_model_id:str, script_txt:str):
    prompt = f"<SCRIPT>\n{script_txt}\n</SCRIPT>\n요구사항: 5씬, 씬당 2~3샷, manim_preset 필수, tone=멘토, pace=중간"
    resp = client.responses.create(
        model=ft_model_id,
        input=prompt,
        response_format={"type":"json_schema","json_schema":{"name":"Storyboard","schema":STORYBOARD_SCHEMA}}
    )
    return resp.output_parsed

if __name__=="__main__":
    ft_model_id = sys.argv[1]
    raw_path    = sys.argv[2]
    script_txt  = open(raw_path,encoding="utf-8").read()
    sb = infer(ft_model_id, script_txt)
    print(json.dumps(sb, ensure_ascii=False, indent=2))
```

&#x20;&#x20;

> 참고: `src/infer_ft.py`도 동일 목적의 실행 스크립트 버전이 있으며, **System/User 프롬프트 스펙·스키마 검증**을 포함한다. &#x20;

---

## 7) 스토리보드 → Manim 변환(렌더 전 단계): `src/storyboard_to_manim.py`

**목적**: 스토리보드(JSON)를 Manim 파이썬 코드로 변환. `FORMULA_REVEAL` 등 프리셋 처리, `MathTex` 미설치 시 `Text`로 대체하는 주석 안내도 포함.&#x20;

**문서 수록 코드(일부):**

```python
import re
HEADER = "from manim import *\n\nclass {klass}(Scene):\n    def construct(self):\n"
def sanitize_title(t): return re.sub(r"[^0-9a-zA-Z]","", t.title())[:30] or "AutoScene"

def emit_line(preset, text):
    text = text.replace('"','\\"')
    if preset == "FORMULA_REVEAL":
        return f'        self.play(Write(MathTex(r"{text}")))\n'
    return f'        self.play(Write(Text("{text}")))\n'

def convert(sb, out_py):
    klass = sanitize_title(sb.get("title","AutoScene"))
    buf = HEADER.format(klass=klass)
    for sc in sb["scenes"]:
        ...
```

&#x20;

---

## 8) “원문 20개 × 증강 9개 → 200” 근거 요약

* **원문 식별**: `data/raw/2.txt ~ 21.txt` 범위가 안내돼 있어 “약 20개”로 운영.&#x20;
* **증강 계수**: 환경변수 지침 “AUG\_PER=9(원본+9=10배)” 및 실행 예시(원본 21개면 189개 생성). 운영 의도는 **원문당 9개 증강**. &#x20;

---

## 9) 튜닝 철학(왜 스토리텔링인가)

* **소수 골드라벨 = 앵커**, **대량 오토라벨 = 패턴 메이커**라는 분업으로, **씬/샷 내레이션과 manim\_preset**의 상관관계를 학습시켜 \*\*“설명 흐름이 있는 스토리보드”\*\*를 산출하게 한다.&#x20;
* 프롬프트 템플릿은 **멘토 톤, 중간 속도, 씬/샷 제약, 스키마 강제**를 포함해 일관된 스토리텔링을 유도한다.&#x20;

---

### 실행 체크리스트(요약)

1. 텍스트 증강(선택): `python -m src.augment_scripts` → `data/raw_aug/`
2. 오토라벨: `python src/auto_label.py` → `data/label_auto/`
3. JSONL 빌드: `python -m src.build_jsonl` → `data/build/train.jsonl, val.jsonl`
4. 파인튜닝: `python src/ft_openai.py` → `ft:...` 모델 ID 확보
5. 추론: `python src/infer_openai.py ft:... data/raw/XX.txt > out/XX_storyboard.json`
   각 단계는 문서에 동일 명령이 기재되어 있다.  &#x20;


----


<파일 사용방법>

# manim-auto v1.2

수학 이미지/문서(PNG·PDF) → **OCR(OpenAI/Tesseract)** → **스토리보드(JSON)** → **Manim 영상(MP4/GIF)** 까지 한 번에 자동화하는 파이프라인입니다. 또한 스토리보드 생성 LLM을 **파인튜닝/데이터 증강**할 수 있는 스크립트가 포함됩니다.

> 현재 확인된 구성으로 **Windows + PowerShell** 기준 명령 예시를 우선 제공합니다. (macOS/Linux도 거의 동일하며, 셸·경로만 바꿔 쓰면 됩니다.)

---

## 핵심 기능

* **E2E 파이프라인**: 이미지·PDF → OCR(JSON/TXT) → LLM 스토리보드(JSON) → Manim 코드 → 영상.
* **LLM 스토리보드 스키마 준수**: `language ∈ {ko,en}`, **scenes 4–6**, **scene당 shots 2–4**, **shot 필수키: `id, narration, manim_preset`**.
* **프리셋 변환기**: `TITLE_CARD`, `BULLET_POINTS`, `FORMULA_REVEAL`, `GEOM_DRAW`, `TRANSFORM`, `GRAPH_PLOT` 등을 Manim 코드로 변환.
* **배치 처리**: `data/raw/*.txt` 일괄 변환.
* **튜닝 데이터 파이프라인**: 라벨(JSON) → 증강 → 학습용 JSONL → 파인튜닝/검증.

---

## 폴더 구조(요약)

```
.
├─ infer_one.py                # 단일 TXT → 스토리보드(JSON)
├─ infer_batch.py              # data/raw/*.txt 일괄 처리
├─ run.py                      # (샘플) 자동 보정 변형 스크립트
├─ out_storyboard.json         # 예시 산출물
├─ data/
│  ├─ pages/                   # 페이지 이미지(PNG)
│  ├─ pages_ocr/               # (선택) OCR JSON
│  ├─ raw/                     # 입력 TXT 스크립트 모음
│  ├─ storyboards/             # 저장된 스토리보드 JSON
│  ├─ label/, label_aug/       # 라벨/증강 라벨(JSON)
│  └─ build/                   # train.jsonl, val.jsonl 등 학습용 산출물
├─ media/                      # Manim 출력(이미지/Tex/텍스트/비디오)
├─ scenes/                     # 샘플 Manim 씬 스크립트들
├─ src/
│  ├─ schema.py                # 스토리보드 JSON 스키마(검증 규칙)
│  ├─ infer_base.py            # LLM 호출 + 스키마검증 유틸
│  ├─ storyboard_to_manim.py   # 스토리보드 → Manim 코드 변환기
│  ├─ augment_labels.py        # (튜닝) 라벨 증강
│  └─ build_jsonl.py           # (튜닝) 학습 JSONL 생성기
└─ tools/
   ├─ ocr_openai.py            # OpenAI Vision OCR (권장)
   ├─ ingest_pdf_ocr.py        # Tesseract+PyMuPDF OCR (옵션)
   └─ pdf_to_png.py            # PDF → PNG 보조
```

---

## 사전 준비

1. **Python 3.11+** 권장 (3.13도 동작 확인)
2. **Manim Community** 설치 및 **FFmpeg** 설치
3. 파이썬 패키지 예시(요지)

```powershell
pip install manim openai jsonschema pymupdf opencv-python pytesseract numpy
```

4. **OpenAI API Key** (세션 주입)

```powershell
$env:OPENAI_API_KEY = 'sk-실제키'
```

* 키는 **ASCII만**, 앞뒤 공백/한글/스마트따옴표가 없어야 합니다.

---

## 빠른 시작(End-to-End)

아래는 \*\*OpenAI Vision OCR 경로(권장)\*\*입니다.

```powershell
# 1) OCR → JSON + TXT
python .\tools\ocr_openai.py --input .\data\pages\_1_3___p14.png `
  --out_json .\out\p14.ocr.json --out_txt .\out\p14.txt

# 2) TXT → 스토리보드(JSON)
python .\infer_one.py --script .\out\p14.txt
# → out\p14.json 생성

# 3) 스토리보드(JSON) → Manim 파이썬 파일
$scene = (python -m src.storyboard_to_manim .\out\p14.json .\out\video.py | Select-Object -Last 1).Trim()
# 콘솔 마지막 줄의 씬 클래스명(예: Autoscene)을 받습니다.

# 4) 렌더(미리보기 / 고속)
manim .\out\video.py $scene -ql -p --media_dir .\media -o p14_test --format=mp4
```

**Tesseract 경로(옵션)**

```powershell
# PDF → (OCR JSONL + PNG) 생성(Tesseract)
python .\tools\ingest_pdf_ocr.py .\data\putnam.pdf .\out\putnam.ocr.jsonl

# JSONL → TXT 변환(간단 변환기 예시)
python - << 'PY'
import json, os
src='out/putnam.ocr.jsonl'; dst='out/putnam.txt'
buf=[]
for ln in open(src,encoding='utf-8'):
    if not ln.strip():
        continue
    o=json.loads(ln)
    t=o.get('plain_text') or o.get('statement') or ''
    if t: buf.append(t)
os.makedirs('out',exist_ok=True)
open(dst,'w',encoding='utf-8').write('\n\n'.join(buf))
print('wrote',dst)
PY

# 이후는 동일: infer_one.py → storyboard_to_manim.py → manim
```

> **배치 처리**: `python .\infer_batch.py` 실행 시 `data/raw/*.txt`를 순회하며 `out/*.json`을 생성합니다.

---

## 스토리보드 스키마(핵심)

* `language`: `"ko" | "en"`
* `scenes`: **4–6개**

  * 각 `scene.shots`: **2–4개**
  * 각 `shot` 필수 키: `id`, `manim_preset`, `narration`
* 허용 `manim_preset`(기본):

  * `TITLE_CARD`, `BULLET_POINTS`, `FORMULA_REVEAL`, `GEOM_DRAW`, `TRANSFORM`, `GRAPH_PLOT`

`src/schema.py`에서 스키마를 엄격히 검증합니다. `infer_one.py`는 LLM 출력이 어긋날 경우 로컬 보정/폴백을 적용해 **항상 유효 JSON**을 저장하도록 설계되어 있습니다.

---

## 변환기(Storyboard → Manim) 확장법

* 파일: `src/storyboard_to_manim.py`
* 프리셋별 `emit_*` 함수를 추가/수정하고, `emit_line()`에 매핑을 더해주면 됩니다.
* 텍스트는 내부에서 `Text()`로 그려지며, 줄바꿈(\n) 시 글머리표 목록으로 렌더링합니다.

예)

```python
def emit_BULLET_POINTS(text):
    lines = "\n".join([f"• {l}" for l in text.split("\n") if l.strip()])
    return f'''
        bullets = Text("{lines}", font_size=36, line_spacing=0.6)
        bullets.to_edge(UP)
        self.play(Write(bullets))
        self.wait(0.5)
'''
```

---

## 모델 튜닝(파인튜닝) 워크플로우

> 저장소에는 라벨/증강/빌드 스크립트가 포함되어 있습니다. 세부 옵션은 각 스크립트의 `-h/--help`를 확인하세요.

### 1) 라벨 → 증강

```powershell
# 예시: 라벨을 규칙적으로 확장
python -m src.augment_labels --in .\data\label\putnam.json `
  --out .\data\label_aug\putnam_aug.json
```

### 2) 학습/검증 JSONL 생성

```powershell
python -m src.build_jsonl `
  --labels .\data\label_aug\putnam_aug.json `
  --train_out .\data\build\train.jsonl `
  --val_out .\data\build\val.jsonl
```

> 포맷은 OpenAI 파인튜닝용 **JSONL**(한 줄에 하나의 학습 샘플). 샘플 구조(의미 예시):

```json
{"messages": [
  {"role": "system", "content": "You convert a math script into a strict Manim storyboard JSON..."},
  {"role": "user",   "content": "<수학 스크립트 텍스트>"},
  {"role": "assistant", "content": "{\"title\":\"...\",\"language\":\"ko\",\"scenes\":[...]}"}
]}
```

### 3) 파인튜닝 실행(예시, Python)

```python
from openai import OpenAI
c=OpenAI()
with open('data/build/train.jsonl','rb') as f:
    job = c.fine_tuning.jobs.create(
        training_file=f,
        model='gpt-4o-mini',  # 베이스
    )
print(job)
```

완료 후 산출된 모델 ID(`ft:...`)를 `OPENAI_MODEL` 환경변수 또는 `infer_one.py`의 기본 모델로 설정합니다.

```powershell
$env:OPENAI_MODEL = 'ft:your-model-id'
```

### 4) 평가

* `data/build/val.jsonl`을 이용해 생성 품질/스키마 적합률을 확인합니다.
* 필요 시 라벨 증강/프롬프트/클램프 로직을 조정합니다.

---

## 자주 묻는 문제(트러블슈팅)

**1) 영상이 검은색/텍스트가 비어 보임**

* 원인: 스토리보드의 `narration`이 비어 있거나 `{}` 같은 플레이스홀더.
* 점검: 아래 스니펫으로 샷 내용을 확인.

```powershell
python - << 'PY'
import json
sb=json.load(open('out/p14.json',encoding='utf-8'))
print('scenes=', len(sb.get('scenes',[])))
print('shots/scene=', [len(s.get('shots',[])) for s in sb.get('scenes',[])])
print([ (sh.get('manim_preset'), (sh.get('narration') or '')[:80])
        for s in sb.get('scenes',[]) for sh in s.get('shots',[]) ][:6])
PY
```

**2) OpenAI 400: `input_image` invalid**

* Chat Completions 비전 입력 타입은 `image_url`이어야 합니다. `tools/ocr_openai.py`는 이미 수정돼 있습니다.

**3) `UnicodeEncodeError: ascii ...` (키 인코딩)**

* 환경변수에 비-ASCII(한글/스마트따옴표/공백)가 섞인 키가 들어간 경우입니다. PowerShell에 작은따옴표로 재설정하세요.

```powershell
$env:OPENAI_API_KEY = 'sk-실제키'
```

**4) `video.py not found` 또는 씬 이름 불일치**

* 변환기 실행 결과 콘솔 마지막 줄의 **씬 클래스명**을 그대로 사용해야 합니다(대소문자 포함).

**5) Tesseract 경로/성능**

* Windows 기본 경로 예시: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`.
* 정확도가 낮으면 **OpenAI Vision OCR** 경로로 전환하세요.

---

## 개발 팁

* PowerShell에서 긴 파이썬 코드는 **here-string**(@'..'@)으로 저장/실행하면 안전합니다.
* Manim 품질 프리셋

  * 빠른 확인: `-ql`
  * 고화질: `-qh` (또는 `-pqh`로 프리뷰 포함)
* 렌더 산출물 경로: `media/videos/<module>/<profile>/<name>.mp4`

---

## 라이선스

* 내부 프로젝트 전제. 외부 배포 전 별도 라이선스 문구 정리 권장.

---

## 변경 이력(요약)

* v1.2 (현재): OpenAI Vision OCR 경로 추가, 스키마 강제 및 폴백 강화, 변환기에서 실제 텍스트 렌더 보장.
* v1.1: 스토리보드 보정 로직 및 배치 처리 개선.

---

## 유지보수/기여 가이드(간단)

* PR 전 `infer_one.py`와 `src/storyboard_to_manim.py`에 대한 **단위 샘플**(1–2 씬)로 동작 확인.
* 프리셋 추가 시: `schema.py`의 enum 업데이트 → 변환기 `emit_*` 구현 → 간단 스냅샷 테스트.

