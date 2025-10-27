from paddleocr import PaddleOCR #pip install "paddleocr>=2.0.1"
from matplotlib import pyplot as plt 
import cv2 #opencv
import os


# 自動取得目前 Python 檔的資料夾
script_dir = os.path.dirname(os.path.abspath(__file__))
print("script_dir:", script_dir)
file_path = os.path.join(script_dir, "test_input_images", "invoice001.png")

#ocr_model = PaddleOCR(use_angle_cls=True, lang='ch')
ocr_model = PaddleOCR(lang='ch')

result = ocr_model.predict(file_path)
print("OCR result:", result)
for line in result[0]:
    print(line)
