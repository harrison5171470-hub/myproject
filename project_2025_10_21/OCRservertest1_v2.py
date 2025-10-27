# OCRservertest1_v2.py
import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

# --------------------------------------------
# 設定你的伺服器 IP
SERVER_IP = "192.168.3.220"
UPLOAD_URL = f"http://{SERVER_IP}:8000/upload"
PROCESS_URL = f"http://{SERVER_IP}:8000/process"
# --------------------------------------------

# 自動取得目前 Python 檔的資料夾
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "test_input_images", "invoice001.png")

# ===== 選字型 =====
def pick_font(box_h_px: float):
    font_candidates = [
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\arialuni.ttf",
    ]
    size = max(10, int(box_h_px * 0.25))
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

# ===== 畫出辨識框與文字 =====
def draw_boxes(img_pil: Image.Image, boxes, line_thickness: int = 5) -> Image.Image:
    draw = ImageDraw.Draw(img_pil)
    for b in boxes:
        x, y, w, h = float(b["x"]), float(b["y"]), float(b["w"]), float(b["h"])
        text = str(b.get("text", ""))
        x2, y2 = x + w, y + h
        draw.rectangle([x, y, x2, y2], outline=(255, 0, 0), width=line_thickness)

        font = pick_font(h)
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        tw, th = (r - l), (b - t)
        pad = max(2, int(h * 0.06))
        tx = int(max(0, min(x2 - tw - pad, img_pil.width - tw - pad)))
        ty = int(max(0, min(y + pad, img_pil.height - th - pad)))
        draw.rectangle([tx - pad, ty - pad, tx + tw + pad, ty + th + pad], fill=(255, 255, 255))
        draw.text((tx, ty), text, font=font, fill=(20, 20, 20))
    return img_pil


def main():
    if not os.path.exists(file_path):
        print(f"[ERROR] Image not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # ---------------------- Step 1: 上傳 ----------------------
    print(f"Uploading: {file_path}")
    with open(file_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(UPLOAD_URL, files=files, timeout=30)
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            sys.exit(1)

    if not data.get("success"):
        print(f"[ERROR] Upload error: {data}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    print(f" Upload success: {filename}")

    # ---------------------- Step 2: OCR 處理 ----------------------
    process_url = f"{PROCESS_URL}/{filename}"
    print(f"Processing OCR via: {process_url}")
    try:
        response = requests.get(process_url, timeout=60)
        data = response.json()
    except Exception as e:
        print(f"[ERROR] Process failed: {e}")
        sys.exit(1)

    if not data.get("success"):
        print(f"[ERROR] OCR error: {data}")
        sys.exit(1)

    print(" OCR process complete")
    boxes = data.get("ocr_boxes", [])

    # ---------------------- Step 3: 畫出結果 ----------------------
    img_pil = Image.open(file_path).convert("RGB")
    img_pil = draw_boxes(img_pil, boxes)

    texts = [b.get("text", "").strip() for b in boxes if b.get("text")]
    all_text = "\n".join(texts)
    print("\n=== OCR 辨識結果 ===")
    print(all_text)

    # ---------------------- Step 4: 顯示 & 儲存 ----------------------
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imshow("OCR Result", img_cv)
    print("Press any key to exit...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join(script_dir, "test_output_images")
    os.makedirs(output_dir, exist_ok=True)
    result_path = os.path.join(output_dir, f"{base_name}_ocr_result.png")
    cv2.imwrite(result_path, img_cv)
    print(f"OCR 圖片已儲存到：{result_path}")

    text_dir = os.path.join(script_dir, "test_output_texts")
    os.makedirs(text_dir, exist_ok=True)
    text_path = os.path.join(text_dir, f"{base_name}_ocr_text.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(all_text)
    print(f"OCR 文字已儲存到：{text_path}")


if __name__ == "__main__":
    main()
