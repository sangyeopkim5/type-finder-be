def restore_backup(json_path):
    backup_path = json_path.replace(".json", "_backup.json")

    print(f"[🔎 복원 시도] 원본: {json_path}")
    print(f"[🔎 복원 시도] 백업: {backup_path}")

    if os.path.exists(backup_path):
        if os.path.exists(json_path):
            os.remove(json_path)
            print(f"[🗑️ 삭제됨] {json_path}")
        shutil.move(backup_path, json_path)
        print(f"[🔁 복원 완료] {json_path} ← {backup_path}")
    else:
        print(f"[⚠️ 백업 파일 없음] {backup_path}")
