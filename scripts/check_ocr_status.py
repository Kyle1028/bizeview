"""
檢查平面圖的 OCR 狀態
"""
import os
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "mysql+pymysql://root:1028@localhost:3306/photobluuring"

def main():
    try:
        from sqlalchemy import create_engine
        from core.models import ExhibitionFloor
        from app import app
    except ImportError as e:
        print(f"匯入錯誤: {e}")
        return 1

    with app.app_context():
        floors = ExhibitionFloor.query.all()
        if not floors:
            print("沒有找到任何樓層")
            return 0

        print(f"找到 {len(floors)} 個樓層\n")
        print("=" * 60)

        for floor in floors:
            print(f"\n樓層: {floor.floor_code}")
            print(f"  展覽 ID: {floor.exhibition_id}")
            print(f"  圖片路徑: {floor.image_path}")
            
            # 檢查 OCR 結果
            if floor.ocr_text_regions:
                print(f"  OCR 結果: 有 ({len(floor.ocr_text_regions)} 個文字區塊)")
                print(f"  前 3 個文字:")
                for i, item in enumerate(floor.ocr_text_regions[:3], 1):
                    print(f"    [{i}] {item.get('text', 'N/A')}")
            else:
                print(f"  OCR 結果: 無")
                
                # 檢查圖片是否存在
                img_path = ROOT / floor.image_path
                if img_path.exists():
                    print(f"  圖片存在: {img_path}")
                    print(f"  建議: 重新上傳此平面圖以觸發 OCR 辨識")
                else:
                    print(f"  圖片不存在: {img_path}")

        print("\n" + "=" * 60)
        return 0

if __name__ == "__main__":
    sys.exit(main())
