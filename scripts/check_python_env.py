"""
檢查 Python 環境和已安裝的套件
"""
import sys
import os
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Python 環境檢查")
print("=" * 60)
print(f"Python 版本: {sys.version}")
print(f"Python 執行檔: {sys.executable}")
print(f"Python 路徑: {sys.path[:3]}")
print()

print("檢查關鍵套件:")
print("-" * 60)

packages_to_check = [
    "rapidocr_onnxruntime",
    "onnxruntime",
    "opencv-python",
    "numpy",
    "flask",
]

for pkg_name in packages_to_check:
    try:
        if pkg_name == "opencv-python":
            import cv2
            print(f"[OK] {pkg_name}: {cv2.__version__}")
        elif pkg_name == "rapidocr_onnxruntime":
            from rapidocr_onnxruntime import RapidOCR
            print(f"[OK] {pkg_name}: 已安裝")
            # 嘗試初始化
            try:
                engine = RapidOCR()
                print(f"  -> 引擎初始化: 成功")
            except Exception as e:
                print(f"  -> 引擎初始化: 失敗 - {e}")
        elif pkg_name == "onnxruntime":
            import onnxruntime
            print(f"[OK] {pkg_name}: {onnxruntime.__version__}")
        elif pkg_name == "numpy":
            import numpy
            print(f"[OK] {pkg_name}: {numpy.__version__}")
        elif pkg_name == "flask":
            import flask
            print(f"[OK] {pkg_name}: {flask.__version__}")
    except ImportError:
        print(f"[FAIL] {pkg_name}: 未安裝")

print()
print("=" * 60)
print("建議:")
print("如果 rapidocr_onnxruntime 未安裝，請執行:")
print(f"  {sys.executable} -m pip install rapidocr_onnxruntime")
print("=" * 60)
