import os
import shutil

def flatten_nested_folders(root_dir):
    print(f"\n🔍 [대상 경로] {root_dir}\n")
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        nested = os.listdir(folder_path)
        if len(nested) == 1:
            inner_path = os.path.join(folder_path, nested[0])
            if os.path.isdir(inner_path):
                print(f"📦 정리 대상: {folder_name}/{nested[0]}")
                
                for subfile in os.listdir(inner_path):
                    src = os.path.join(inner_path, subfile)
                    dst = os.path.join(folder_path, subfile)
                    print(f"    → 이동: {src} → {dst}")
                    shutil.move(src, dst)

                shutil.rmtree(inner_path)
                print(f"    ⛔ 중간 폴더 삭제됨: {inner_path}")
        else:
            print(f"✅ 이미 정상: {folder_name}")

# ✅ 경로만 TS 쪽으로 바꾸면 끝
flatten_nested_folders("원천데이터")
