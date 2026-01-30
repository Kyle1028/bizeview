"""
直接測試 OCR 功能
"""
import os
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/test_ocr_direct.py <圖片路徑>")
        print("範例: python scripts/test_ocr_direct.py exhibitions/5/F001_floor.jpg")
        return 1
    
    image_path = Path(sys.argv[1])
    if not image_path.is_absolute():
        image_path = ROOT / image_path
    
    if not image_path.exists():
        print(f"錯誤：找不到圖片 {image_path}")
        return 1
    
    print(f"測試圖片: {image_path}")
    print("=" * 60)
    
    try:
        from core.floor_plan_ocr import floor_plan_text_regions, _get_engine
        
        # 檢查引擎
        engine = _get_engine()
        if engine is None:
            print("錯誤：OCR 引擎未載入")
            print("請確認 rapidocr_onnxruntime 已安裝：pip install rapidocr_onnxruntime")
            return 1
        
        print("✓ OCR 引擎載入成功")
        print()
        
        # 進行 OCR 辨識
        print("開始 OCR 辨識...")
        ocr_regions = floor_plan_text_regions(image_path)
        
        print(f"辨識結果數量: {len(ocr_regions)}")
        print()
        
        if ocr_regions:
            print("辨識到的文字：")
            print("-" * 60)
            for i, (bbox, text) in enumerate(ocr_regions, 1):
                bbox_str = f"bbox: {bbox}" if bbox else "bbox: []"
                print(f"[{i:3d}] {text}")
                if bbox:
                    print(f"      {bbox_str}")
            print("-" * 60)
            print(f"\n總共辨識到 {len(ocr_regions)} 個文字區塊")
        else:
            print("未辨識到任何文字")
            print("\n可能的原因：")
            print("1. 圖片上確實沒有文字")
            print("2. OCR 引擎載入失敗")
            print("3. 圖片格式不支援")
            print("4. 圖片解析度過低或過高")
        
        return 0
    except Exception as e:
        import traceback
        print(f"錯誤：{e}")
        print("\n詳細錯誤信息：")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
