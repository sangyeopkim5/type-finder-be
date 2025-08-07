import json
from PIL import Image
import os

# ✅ 경로 설정
base_dir = r"G:\내 드라이브\초개인화 교육 시스템\수식, 도형, 낙서기호, OCR 데이터\038.수식, 도형, 낙서기호 OCR 데이터\01.데이터\1.Training"
json_path = os.path.join(base_dir, "라벨링데이터", "TL_고1", "1010", "M_P_h1_1010_00001.json")
image_path = os.path.join(base_dir, "원천데이터", "TS_고1","1010", "M_P_h1_1010_00001.png")
output_txt_path = os.path.join(base_dir, "YOLO_labels", "M_P_h1_1010_00001.txt")

# 출력 디렉토리 생성
os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

# ✅ YOLO 변환 함수
def convert_box_to_yolo(box, img_width, img_height):
    x_coords = [pt[0] for pt in box]
    y_coords = [pt[1] for pt in box]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    x_center = (x_min + x_max) / 2 / img_width
    y_center = (y_min + y_max) / 2 / img_height
    width = (x_max - x_min) / img_width
    height = (y_max - y_min) / img_height
    return x_center, y_center, width, height

# ✅ 이미지 크기 읽기
with Image.open(image_path) as img:
    img_width, img_height = img.size

# ✅ JSON 읽기
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ✅ YOLO 라벨 생성
yolo_lines = []
for segment in data["segments"]:
    box = segment["box"]
    type_detail = segment["type_detail"]

    if type_detail not in ["수식", "텍스트"]:
        continue  # 도형 등은 무시

    cls = 0 if type_detail == "수식" else 1
    x, y, w, h = convert_box_to_yolo(box, img_width, img_height)
    yolo_lines.append(f"{cls} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")

# ✅ 저장
with open(output_txt_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(yolo_lines))

print(f"✅ YOLO 변환 완료 → {output_txt_path}") 