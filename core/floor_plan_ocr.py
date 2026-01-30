"""
平面圖文字偵測模組：使用 RapidOCR 判斷平面圖上是否有字
供建立／編輯展覽時上傳平面圖後提示使用者，不阻擋流程。
"""
from pathlib import Path
from typing import Union, List, Tuple, Optional

import numpy as np

# 延遲載入 RapidOCR，失敗時不影響其他功能
_ocr_engine = None


def _get_engine():
    """取得 RapidOCR 引擎（單例，延遲載入）"""
    global _ocr_engine
    if _ocr_engine is not None:
        return _ocr_engine
    try:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
        return _ocr_engine
    except ImportError as e:
        import logging
        logging.error(f"無法匯入 rapidocr_onnxruntime: {e}")
        logging.error("請確認已安裝: pip install rapidocr_onnxruntime")
        return None
    except Exception as e:
        import logging
        logging.error(f"RapidOCR 引擎初始化失敗: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None


def _image_to_array(path: Path) -> Optional[np.ndarray]:
    """從檔案路徑讀取為 BGR 影像（OpenCV 格式），供 OCR 使用"""
    try:
        import cv2
        img = cv2.imread(str(path))
        if img is None:
            return None
        return img
    except Exception:
        return None


def _maybe_resize(img: np.ndarray, max_side: int = 2000) -> np.ndarray:
    """過大圖片縮小，避免 OCR 記憶體或模型限制"""
    try:
        import cv2
        h, w = img.shape[:2]
        if max(h, w) <= max_side:
            return img
        scale = max_side / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    except Exception:
        return img


def floor_plan_has_text(path_or_image: Union[str, Path, np.ndarray]) -> bool:
    """
    判斷平面圖上是否偵測到文字。

    參數:
        path_or_image: 平面圖檔案路徑（str 或 Path）或 BGR 影像陣列（numpy ndarray）

    回傳:
        True 若偵測到至少一處文字，否則 False。
        若 OCR 未安裝、載入失敗或執行錯誤，回傳 False（不拋出例外）。
    """
    engine = _get_engine()
    if engine is None:
        return False

    if isinstance(path_or_image, (str, Path)):
        path = Path(path_or_image)
        if not path.exists():
            return False
        img = _image_to_array(path)
        if img is None:
            return False
        path_str = str(path.resolve())
    elif isinstance(path_or_image, np.ndarray):
        img = path_or_image
        path_str = None
    else:
        return False

    img = _maybe_resize(img)

    try:
        # 部分 RapidOCR 版本接受路徑字串，先試路徑再試陣列
        out = None
        if path_str is not None:
            try:
                out = engine(path_str)
            except Exception:
                pass
        if out is None:
            out = engine(img)
        result = out[0] if isinstance(out, (list, tuple)) and len(out) > 0 else out
        if result is None:
            return False
        if isinstance(result, (list, tuple)) and len(result) > 0:
            return True
        return False
    except Exception:
        return False


def floor_plan_text_regions(path_or_image: Union[str, Path, np.ndarray]) -> List[Tuple[list, str]]:
    """
    辨識平面圖上的文字區塊與內容（供日後擴充，例如建議區域名稱）。
    返回的 bbox 座標是相對於原圖的，即使圖片被縮放也會轉換回原圖座標。

    參數:
        path_or_image: 平面圖檔案路徑或 BGR 影像陣列

    回傳:
        列表，每項為 (bbox, text)。bbox 是相對於原圖的座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]。
        若失敗或無文字則回傳 []。
    """
    engine = _get_engine()
    if engine is None:
        return []

    # 記錄原圖尺寸
    original_img = None
    if isinstance(path_or_image, (str, Path)):
        path = Path(path_or_image)
        if not path.exists():
            return []
        original_img = _image_to_array(path)
        if original_img is None:
            return []
        img = original_img.copy()
        path_str = str(path.resolve())
        original_h, original_w = original_img.shape[:2]
    elif isinstance(path_or_image, np.ndarray):
        original_img = path_or_image
        img = original_img.copy()
        path_str = None
        original_h, original_w = original_img.shape[:2]
    else:
        return []

    # 縮放圖片（如果需要）
    resized_img = _maybe_resize(img)
    resized_h, resized_w = resized_img.shape[:2]
    
    # 計算縮放比例
    scale_x = original_w / resized_w if resized_w > 0 else 1.0
    scale_y = original_h / resized_h if resized_h > 0 else 1.0

    try:
        raw = None
        used_path = False
        
        if path_str is not None:
            try:
                # 嘗試使用原圖路徑（RapidOCR 可能會自動處理）
                raw = engine(path_str)
                # 如果使用原圖路徑，座標已經是原圖座標，不需要縮放
                scale_x = scale_y = 1.0
                used_path = True
            except Exception as e:
                import logging
                logging.debug(f"使用路徑辨識失敗，改用圖片陣列: {e}")
                pass
        
        if raw is None:
            raw = engine(resized_img)
        
        # RapidOCR 返回格式：(result, elapse)
        # result 是一個列表，每個元素是 [bbox, text, score]
        # bbox 是 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        if raw is None:
            return []
        
        # 處理 RapidOCR 返回格式
        result = None
        if isinstance(raw, (list, tuple)):
            if len(raw) > 0:
                result = raw[0]  # 第一個元素是結果列表
        else:
            result = raw
        
        if result is None or not isinstance(result, (list, tuple)):
            return []
        
        out = []
        for item in result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                bbox = item[0]
                text = item[1]
                
                # 確保文字不為空
                if not text or not str(text).strip():
                    continue
                
                text_str = str(text).strip()
                
                # 將 bbox 座標轉換回原圖座標
                if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    original_bbox = []
                    for point in bbox[:4]:
                        if isinstance(point, (list, tuple)) and len(point) >= 2:
                            # 轉換座標：縮放後的座標 * 縮放比例 = 原圖座標
                            x = float(point[0]) * scale_x
                            y = float(point[1]) * scale_y
                            original_bbox.append([x, y])
                        else:
                            # 如果點格式不對，跳過這個結果
                            original_bbox = None
                            break
                    
                    if original_bbox and len(original_bbox) == 4:
                        out.append((original_bbox, text_str))
                    else:
                        # bbox 格式不正確，但仍然保存文字（使用空 bbox）
                        import logging
                        logging.warning(f"OCR bbox 格式不正確，文字: {text_str}, bbox: {bbox}")
                        out.append(([], text_str))
                else:
                    # bbox 格式不正確，但仍然保存文字
                    import logging
                    logging.warning(f"OCR bbox 不是列表或長度不足，文字: {text_str}, bbox: {bbox}")
                    out.append(([], text_str))
        
        return out
    except Exception as e:
        import logging
        import traceback
        logging.error(f"OCR 辨識過程發生錯誤: {e}\n{traceback.format_exc()}")
        return []
