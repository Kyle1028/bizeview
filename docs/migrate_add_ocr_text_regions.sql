-- ============================================================
-- 遷移：新增 OCR 文字辨識結果欄位（既有資料庫請執行此檔一次）
-- 若 exhibition_floors.ocr_text_regions 欄位已存在，請略過此語句。
-- ============================================================

-- 在 exhibition_floors 表新增 OCR 文字辨識結果欄位
-- 格式：JSON，包含文字內容和位置座標
-- [{"text": "文字內容", "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]}, ...]
ALTER TABLE exhibition_floors
    ADD COLUMN ocr_text_regions JSON NULL AFTER grid_size;
