"""
驗證 OCR 欄位遷移是否成功
"""
import os
import sys
import io
from pathlib import Path

# 設定輸出編碼為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "mysql+pymysql://root:1028@localhost:3306/photobluuring"

def main():
    try:
        from sqlalchemy import create_engine, inspect
    except ImportError:
        print("請先安裝: pip install sqlalchemy pymysql")
        return 1

    engine = create_engine(DATABASE_URL)
    insp = inspect(engine)
    
    try:
        columns = [c["name"] for c in insp.get_columns("exhibition_floors")]
        if "ocr_text_regions" in columns:
            print("[OK] 欄位 exhibition_floors.ocr_text_regions 已存在")
            # 檢查欄位類型
            for col in insp.get_columns("exhibition_floors"):
                if col["name"] == "ocr_text_regions":
                    print(f"  類型: {col['type']}")
                    print(f"  可為空: {col['nullable']}")
            return 0
        else:
            print("[FAIL] 欄位 exhibition_floors.ocr_text_regions 不存在")
            print(f"現有欄位: {', '.join(columns)}")
            return 1
    except Exception as e:
        print(f"檢查時發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
