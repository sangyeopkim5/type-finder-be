import os
import json
import shutil
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# ✅ 경로 설정
ocr_base = r"G:\내 드라이브\초개인화 교육 시스템\수식, 도형, 낙서기호, OCR 데이터\038.수식, 도형, 낙서기호 OCR 데이터\01.데이터\1.Training"
yolo_base = r"G:\내 드라이브\초개인화 교육 시스템\수식, 도형, 낙서기호,Yolodata\dataset\1.Training"

# ✅ 대상 폴더
targets = {
    "TL_고1": list(range(1010, 1016))
}

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

# ✅ 단일 파일 처리 함수
def process_file(group, chapter, filename):
    chapter_str = str(chapter)

    json_path = os.path.join(ocr_base, "라벨링데이터", group, chapter_str, filename)
    image_name = filename.replace(".json", ".png")
    image_path = os.path.join(ocr_base, "원천데이터", group.replace("TL", "TS"), chapter_str, image_name)

    yolo_label_path = os.path.join(yolo_base, "라벨링데이터", group, chapter_str, filename.replace(".json", ".txt"))
    yolo_image_path = os.path.join(yolo_base, "원천데이터", group, chapter_str, image_name)

    try:
        with Image.open(image_path) as img:
            w, h = img.size
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        yolo_lines = []
        for seg in data["segments"]:
            type_label = seg["type_detail"]
            cls = 0 if type_label == "수식" else 1 if type_label == "텍스트" else 2
            x, y, width, height = convert_box_to_yolo(seg["box"], w, h)
            yolo_lines.append(f"{cls} {x:.6f} {y:.6f} {width:.6f} {height:.6f}")

        with open(yolo_label_path, "w", encoding="utf-8") as f:
            f.write("\n".join(yolo_lines))
        shutil.copy2(image_path, yolo_image_path)

        print(f"✅ 완료: {filename} → {chapter_str}")
    except Exception as e:
        print(f"❌ 오류 발생 ({filename}): {e}")

# ✅ 전체 병렬 실행
def run_parallel_conversion():
    tasks = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        for group, chapters in targets.items():
            for chapter in chapters:
                chapter_str = str(chapter)

                json_dir = os.path.join(ocr_base, "라벨링데이터", group, chapter_str)
                img_dir = os.path.join(ocr_base, "원천데이터", group.replace("TL", "TS"), chapter_str)
                yolo_label_dir = os.path.join(yolo_base, "라벨링데이터", group, chapter_str)
                yolo_image_dir = os.path.join(yolo_base, "원천데이터", group, chapter_str)

                os.makedirs(yolo_label_dir, exist_ok=True)
                os.makedirs(yolo_image_dir, exist_ok=True)

                if not os.path.exists(json_dir) or not os.path.exists(img_dir):
                    print(f"🚫 경로 없음: {json_dir} 또는 {img_dir}")
                    continue

                for filename in os.listdir(json_dir):
                    if filename.endswith(".json") and "backup" not in filename:
                        tasks.append(executor.submit(process_file, group, chapter, filename))

    print(f"🧠 총 작업 개수: {len(tasks)}개 병렬 처리 완료됨")

# ✅ 실행
if __name__ == "__main__":
    run_parallel_conversion()
