#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復展覽封面圖片路徑的腳本
檢查 exhibitions/tadte_2025/cover.jpg 是否存在，如果存在但資料庫中沒有正確路徑，則更新資料庫
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app
from core.models import db, Exhibition

def fix_exhibition_cover():
    """修復展覽封面圖片路徑"""
    with app.app_context():
        # 查找所有展覽
        exhibitions = Exhibition.query.all()
        
        print(f"找到 {len(exhibitions)} 個展覽")
        
        # 檢查 exhibitions/tadte_2025/cover.jpg
        cover_path = BASE_DIR / "exhibitions" / "tadte_2025" / "cover.jpg"
        
        if not cover_path.exists():
            print(f"錯誤：封面圖片不存在於 {cover_path}")
            return
        
        print(f"找到封面圖片：{cover_path}")
        
        # 計算相對路徑
        relative_path = cover_path.relative_to(BASE_DIR)
        print(f"相對路徑：{relative_path}")
        
        # 查找標題包含 "台北國際航太" 或 "tadte" 的展覽
        target_exhibition = None
        for exhibition in exhibitions:
            if "台北國際航太" in exhibition.title or "tadte" in exhibition.title.lower():
                target_exhibition = exhibition
                break
        
        if not target_exhibition:
            print("錯誤：找不到對應的展覽")
            print("所有展覽標題：")
            for ex in exhibitions:
                print(f"  - ID: {ex.id}, 標題: {ex.title}, 封面: {ex.cover_image}")
            return
        
        print(f"找到目標展覽：ID={target_exhibition.id}, 標題={target_exhibition.title}")
        print(f"目前資料庫中的封面路徑：{target_exhibition.cover_image}")
        
        # 檢查是否需要更新
        if target_exhibition.cover_image != str(relative_path):
            print(f"更新封面圖片路徑...")
            target_exhibition.cover_image = str(relative_path)
            try:
                db.session.commit()
                print(f"[成功] 更新封面圖片路徑為：{relative_path}")
            except Exception as e:
                db.session.rollback()
                print(f"[失敗] 更新失敗：{e}")
        else:
            print("封面圖片路徑已正確，無需更新")

if __name__ == "__main__":
    fix_exhibition_cover()
