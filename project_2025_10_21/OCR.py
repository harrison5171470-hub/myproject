
# ========================================
# OCR 圖片文字辨識範例
# 作者：徐浩瑜
# 功能：
#   1. 自動尋找當前腳本所在路徑
#   2. 打開圖片 → 灰階 → 提升對比 → 銳化 → 放大
#   3. 呼叫 Tesseract OCR 辨識中英文
#   4. 嘗試用正則表達式擷取金額字樣
# ========================================

# (1) --- 套件導入 ---

# OCRtest\Scripts\activate

import pytesseract  # Python 的 Tesseract OCR 接口
from PIL import Image, ImageEnhance, ImageFilter  # 影像處理套件 Pillow
import re          # 正則表達式，用於擷取金額
import os          # 系統路徑操作

# (2) --- 指定 tesseract.exe 執行檔路徑 ---
#  請確認你的安裝目錄一致
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# (3) --- 取得當前程式執行所在目錄 ---
# 若在 VSCode / Jupyter 執行，__file__ 可能不存在
if '__file__' in globals():
    # 自動取得目前 Python 檔的資料夾
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("script_dir:", script_dir)
else:
    script_dir = os.getcwd()  # 互動式環境使用當前工作目錄

# (4) --- 設定圖片路徑 ---
#file_path = r"E:\projects\myproject\project_2025_10_21\test_input_images\invoice001.png"
file_path = os.path.join(script_dir, "test_input_images", "invoice001.png")
print("file_path:", file_path, "exists:", os.path.exists(file_path))

# (5) --- 確認圖片是否存在 ---
print("DEBUG - img_path:", file_path)
print("DEBUG - exists:", os.path.exists(file_path))

if not os.path.exists(file_path):
    raise FileNotFoundError(f"找不到圖片: {file_path}")

# (6) --- 開啟圖片 ---
img = Image.open(file_path)

# (7) --- 圖片預處理 ---
# 目的：幫助 OCR 辨識更清楚的文字
# Step 1：轉灰階，去除顏色干擾
img_gray = img.convert("L")

# Step 2：提高對比 (1.0 = 原始對比度, 建議 1.5~3.0)
img_contrast = ImageEnhance.Contrast(img_gray).enhance(2)

# Step 3：銳化邊緣，讓文字邊緣更明顯
img_sharp = img_contrast.filter(ImageFilter.SHARPEN)

# Step 4：放大圖片（有助於 OCR 判別細字）
w, h = img_sharp.size
img_big = img_sharp.resize((w * 2, h * 2))

# ⚠️ 選擇性：如果圖片背景太花，可以考慮先二值化
# threshold = 180
# img_bw = img_big.point(lambda x: 0 if x < threshold else 255, '1')

# (8) --- OCR 辨識 ---
# lang 可依需求設定：
#   'eng' 英文
#   'chi_sim' 簡體中文
#   'chi_tra' 繁體中文
#   'eng+chi_tra' 同時辨識中英文（推薦）
#   若缺字體可至 tessdata 目錄下載語言包

print("\n=== OCR 辨識中... ===")

# 英文辨識
#text_en = pytesseract.image_to_string(img_big, lang='eng')
#print("\n[英文辨識結果]")
#print(text_en)

# 中文辨識
#text_chi = pytesseract.image_to_string(img_big, lang='chi_tra')
#print("\n[中文辨識結果]")
#print(text_chi)

text_mixed = pytesseract.image_to_string(img_big, lang='eng+chi_tra')
print("\n[中英文混合辨識結果]", text_mixed)

# (9) --- 正則表達式擷取金額 ---
# 正則說明：
# \$          ：匹配美元符號
# \s?         ：可有可無的空白
# \d+         ：一個或多個數字
# (?:\.\d{2})?：可選的小數點與兩位數
amount = re.findall(r'\$\s?\d+(?:\.\d{2})?', text_mixed)
print("\n[擷取結果]")
print("辨識金額：", amount)
# (9.1) --- 擷取日期 ---
dates = re.findall(r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}', text_mixed)
print("\n[擷取結果 - 日期]")
print("辨識日期：", dates)

# (9.2) --- 擷取公司名稱 ---
company = re.findall(r'[\u4e00-\u9fa5A-Za-z\s]{2,10}(?:股\s*份)?\s*有限\s*公司', text_mixed)
print("\n[擷取結果 - 公司名稱]")
print("辨識公司名稱：", company)


# (10) --- 顯示原始輸出 (除錯用) ---
print("\n=== OCR 原始輸出 repr() ===")
print(repr(text_mixed))

# (11) --- 附加建議 ---
# 若辨識結果仍不理想，可嘗試：
#   1. 改用 lang='eng+chi_tra'
#   2. 將圖片背景改為白底黑字
#   3. 調整亮度、對比度參數
#   4. 用 cv2 (OpenCV) 先二值化、降噪再丟給 Tesseract
