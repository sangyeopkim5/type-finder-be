#손고1데이터만 삭제
import os

yolo_label_dir = r"G:\내 드라이브\초개인화 교육 시스템\수식, 도형, 낙서기호,Yolodata\dataset\1.Training\라벨링데이터\TL_고1\1015"

deleted = 0
for filename in os.listdir(yolo_label_dir):
    if filename.endswith(".txt"):
        file_path = os.path.join(yolo_label_dir, filename)
        os.remove(file_path)
        print(f"[🗑️ 삭제됨] {file_path}")
        deleted += 1

print(f"\n✅ 총 {deleted}개 YOLO 라벨 파일 삭제 완료.")
