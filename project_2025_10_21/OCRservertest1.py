# OCRservertest1.py
# 環境啟動 OCRtest\Scripts\activate
# pip3 install requests pillow opencv-python

import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2




url = "http://192.168.3.220:8000/upload"  # Replace with your IP address


#print("cwd:", os.getcwd())


# 自動取得目前 Python 檔的資料夾
script_dir = os.path.dirname(os.path.abspath(__file__))
print("script_dir:", script_dir)

#file_path = r"E:\projects\myproject\project_2025_10_21\test_input_images\invoice001.png"
file_path = os.path.join(script_dir, "test_input_images", "invoice001.png")
print("file_path:", file_path, "exists:", os.path.exists(file_path))

# ===== Select font (supports Chinese and English), font size auto-scales with box height =====
def pick_font(box_h_px: float):
    font_candidates = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Windows
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\arialuni.ttf",
        # Noto
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        
        
    ]
    size = max(10, int(box_h_px * 0.25))  # Small font size = 25% of box height (minimum 10pt)
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

# ===== Draw box and small text =====
# 定義 draw_boxes() 函數，用 PIL 畫框與文字標籤。
# 讓你在圖片上清楚看到哪裡被辨識出來。
def draw_boxes(img_pil: Image.Image, boxes, line_thickness: int = 5) -> Image.Image:
    draw = ImageDraw.Draw(img_pil)
    for b in boxes:
        try:
            x = float(b["x"]); y = float(b["y"])
            w = float(b["w"]); h = float(b["h"])
            text = str(b.get("text", ""))
        except Exception:
            continue

        # Red bounding box
        x2, y2 = x + w, y + h
        draw.rectangle([x, y, x2, y2], outline=(255, 0, 0), width=line_thickness)

        # Top-right label
        font = pick_font(h)
        # Text size
        # textbbox returns (l, t, r, b)
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        tw, th = (r - l), (b - t)
        pad = max(2, int(h * 0.06))

        # Align label to top-right, not exceeding box or image edge
        tx = int(max(0, min(x2 - tw - pad, img_pil.width - tw - pad)))
        ty = int(max(0, min(y + pad, img_pil.height - th - pad)))

        # White background
        draw.rectangle([tx - pad, ty - pad, tx + tw + pad, ty + th + pad], fill=(255, 255, 255))
        draw.text((tx, ty), text, font=font, fill=(20, 20, 20))
    return img_pil
# ===== Main function =====
def main():
    if not os.path.exists(file_path):
        print(f"[ERROR] Image not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # 1) Upload
    with open(file_path, "rb") as f:
        files = {"file": f}
        headers = {"Accept": "application/json"}
        try:
            response = requests.post(url, files=files, headers=headers, timeout=60)
        except requests.RequestException as e:
            print(f"[ERROR] Request failed: {e}", file=sys.stderr)
            sys.exit(2)

    print("status code:", response.status_code)

    # 2) Check HTTP and JSON
    if response.status_code != 200:
        print("response:", response.text[:500])
        sys.exit(3)

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Not JSON response")
        print("response:", response.text[:500])
        sys.exit(4)

    if not data.get("success", False):
        print("[ERROR] Server returned failure:", data)
        sys.exit(5)

    print("response ok")
    print("Server returned JSON:", data)

    # 3) Load original image (using PIL)
    img_pil = Image.open(file_path).convert("RGB")

    # If server returns different dimensions (should usually match), use server dimensions
    W = int(data.get("image_width", img_pil.width))
    H = int(data.get("image_height", img_pil.height))
    if (W, H) != (img_pil.width, img_pil.height):
        img_pil = img_pil.resize((W, H), Image.BICUBIC)
 
    boxes = data.get("ocr_boxes", [])
    img_pil = draw_boxes(img_pil, boxes)
    
    # 4) 提取 OCR 辨識文字
    texts = [b.get("text", "").strip() for b in boxes if b.get("text")]
    all_text = "\n".join(texts)
    print("\n=== OCR 辨識文字輸出（後續可給正則或規則引擎使用） ===")
    print(all_text)

    # 5) Display
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imshow("OCR Preview", img_cv)
    print("Press any key on the image window to exit...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 5) save result image and text file
    
    # 取得原始檔名（不含路徑與副檔名）
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    # 組合新的輸出檔名
    output_image_name = f"{base_name}_ocr_result.png"
    output_text_name = f"{base_name}_ocr_text.txt"
    
    # 組合完整路徑
    output_dir1 = "E:/projects/myproject/project_2025_10_21/test_output_images"
    os.makedirs(output_dir1, exist_ok=True)
    image_output_path = os.path.join(output_dir1, output_image_name)
    cv2.imwrite(image_output_path, img_cv)
    print(f"OCR 圖片已儲存到：{image_output_path}")
    
    output_dir2 = "E:/projects/myproject/project_2025_10_21/test_output_texts"
    os.makedirs(output_dir2, exist_ok=True)
    text_output_path = os.path.join(output_dir2, output_text_name)
    with open(text_output_path, "w", encoding="utf-8") as f:
        f.write(all_text)
    print(f"OCR 文字已儲存到：{text_output_path}")

# 只有當你用python OCRservertest1.py直接執行這個檔案時，才會去執行 main() ，也就是整個程式。
if __name__ == "__main__":
    main()