import os, json, re, base64, shutil, uuid
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# 🔑 API Key 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def crop_image(image_path, box, save_path):
    with Image.open(image_path) as img:
        x1, y1 = box[0]
        x3, y3 = box[2]
        crop = img.crop((x1, y1, x3, y3))
        crop.save(save_path)
        return save_path

def ask_gpt_formula_index(image_path, equation):
    with open(image_path, "rb") as img_file:
        base64_img = base64.b64encode(img_file.read()).decode("utf-8")

    prompt = f"""
이미지 안의 수식과 텍스트가 한 줄에 나란히 있을 때,  
수식이 몇 번째에 위치하는지 숫자로만 알려줘.  
(예: 수식이 맨 앞이면 1, 그다음이면 2, 중간이면 3...)  
반드시 숫자 하나만 출력해줘.  
수식: {equation}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                    ]
                }
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()
        match = re.search(r"\d+", content)
        return int(match.group()) if match else 1
    except Exception as e:
        print(f"[❌ GPT Error] {e}")
        return 1

def split_box_by_index(box, formula_index, total_parts=2):
    x1, y1 = box[0]
    x2, _  = box[1]
    x3, y3 = box[2]

    width = x2 - x1
    part_width = width // total_parts

    fx1 = x1 + (formula_index - 1) * part_width
    fx2 = fx1 + part_width

    formula_box = [[fx1, y1], [fx2, y1], [fx2, y3], [fx1, y3]]

    if formula_index == 1:
        text_box = [[fx2, y1], [x2, y1], [x3, y3], [fx2, y3]]
    else:
        text_box = [[x1, y1], [fx1, y1], [fx1, y3], [x1, y3]]

    return formula_box, text_box

def extract_parts(equation):
    match = re.search(r'(\$.*?\$)', equation)
    if match:
        return match.group(1).strip(), equation.replace(match.group(1), "").strip()
    return None, equation.strip()

def process_single_file(json_path, image_path, crop_folder):
    if not os.path.exists(json_path):
        print(f"[❌ JSON 파일 없음] {json_path}")
        return
    if not os.path.exists(image_path):
        print(f"[❌ 이미지 없음] {image_path}")
        return

    # ✅ 백업
    backup_path = json_path.replace(".json", "_backup.json")
    if not os.path.exists(backup_path):
        shutil.copyfile(json_path, backup_path)
        print(f"[📦 백업 생성됨] {backup_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filename = os.path.splitext(os.path.basename(json_path))[0]
    new_segments = []
    box_counter = 1

    for idx, seg in enumerate(data.get("segments", [])):
        if seg["type_detail"] == "수식/텍스트":
            formula, text = extract_parts(seg["equation"])

            if formula and not text:
                new_segments.append({
                    "box": seg["box"],
                    "type_detail": "수식",
                    "equation": formula,
                    "box_index": box_counter
                })
                box_counter += 1
                continue

            elif text and not formula:
                new_segments.append({
                    "box": seg["box"],
                    "type_detail": "텍스트",
                    "equation": text,
                    "box_index": box_counter
                })
                box_counter += 1
                continue

            elif formula and text:
                crop_name = f"{filename}_{idx}_{uuid.uuid4().hex[:6]}.png"
                crop_path = os.path.join(crop_folder, crop_name)
                crop_image(image_path, seg["box"], crop_path)

                index = ask_gpt_formula_index(crop_path, seg["equation"])
                print(f"[🔍 수식 위치 인덱스] index={index} for equation: {formula}")

                box_f, box_t = split_box_by_index(seg["box"], index)

                new_segments.append({
                    "box": box_f,
                    "type_detail": "수식",
                    "equation": formula,
                    "box_index": box_counter
                })
                box_counter += 1

                new_segments.append({
                    "box": box_t,
                    "type_detail": "텍스트",
                    "equation": text,
                    "box_index": box_counter
                })
                box_counter += 1
            else:
                new_segments.append(seg)
                seg["box_index"] = box_counter
                box_counter += 1
        else:
            seg["box_index"] = box_counter
            new_segments.append(seg)
            box_counter += 1

    data["segments"] = new_segments

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[✅ 저장 완료] {json_path}")

if __name__ == "__main__":
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    json_path = os.path.join(base, "라벨링데이터", "TL_고1", "1010", "M_P_h1_1010_00001.json")
    image_path = os.path.join(base, "원천데이터", "TS_고1", "1010", "M_P_h1_1010_00001.png")
    crop_folder = os.path.join(base, "temp_crops")

    os.makedirs(crop_folder, exist_ok=True)
    process_single_file(json_path, image_path, crop_folder)
