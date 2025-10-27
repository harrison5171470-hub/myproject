# OCR_server_v2.py
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles # pip install fastapi[all]
from fastapi.templating import Jinja2Templates # pip install jinja2
from fastapi import Body
from paddleocr import PaddleOCR
from PIL import Image
import os
import traceback
import numpy as np
import uvicorn
# 建立 FastAPI 應用
app = FastAPI()

# ---------- 路徑設定 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded")  # ← 修改這裡
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 靜態資源與模板資料夾
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

#app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploaded", StaticFiles(directory=UPLOAD_DIR), name="uploaded")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ---------- 首頁 ----------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index01.html", {"request": request})

# ---------- 初始化 OCR ----------
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# ---------- 上傳檔案 ----------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return JSONResponse({
            "success": True,
            "filename": file.filename,  #
            "message": f"File '{file.filename}' uploaded successfully.",
            "file_path": file_path
        })
    except Exception as exc:
        tb = traceback.format_exc()
        return JSONResponse({"success": False, "error": str(exc), "traceback": tb}, status_code=500)

# ---------- 下載檔案 ----------
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse({"success": False, "error": "File not found"})
    return FileResponse(file_path)

# ---------- OCR 處理 ----------
@app.get("/process/{filename}")
async def process_file(filename: str):
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        print(f"[DEBUG] Received OCR request for: {file_path}")

        if not os.path.exists(file_path):
            print("[ERROR] File not found on server!")
            return JSONResponse({"success": False, "error": "File not found"})

        image = Image.open(file_path).convert("RGB")
        print(f"[DEBUG] Image opened, size={image.size}, mode={image.mode}")

        # 執行 OCR
        result = ocr.ocr(np.array(image))
        print(f"[DEBUG] Raw OCR result keys: {result[0].keys()}")

        if not result or not isinstance(result[0], dict):
            print("[WARNING] Unexpected OCR result format")
            return JSONResponse({"success": False, "error": "Unexpected OCR result format"})

        # 新版 PaddleOCR 回傳格式解析
        boxes = result[0].get('rec_boxes', [])
        texts = result[0].get('rec_texts', [])
        scores = result[0].get('rec_scores', [])
        print(f"[DEBUG] Found {len(texts)} text lines")

        ocr_boxes = []
        for box, text, score in zip(boxes, texts, scores):
            box = np.array(box).flatten()
            x1, y1 = min(box[0::2]), min(box[1::2])
            x2, y2 = max(box[0::2]), max(box[1::2])
            ocr_boxes.append({
                "x": int(x1),
                "y": int(y1),
                "w": int(x2 - x1),
                "h": int(y2 - y1),
                "text": text,
                "confidence": float(score)
            })
            print(f"[BOX] {text} ({score:.3f})")

        return JSONResponse({
            "success": True,
            "ocr_engine": "PaddleOCR v5",
            "image_width": image.width,
            "image_height": image.height,
            "ocr_boxes": ocr_boxes
        })

    except Exception as exc:
        tb = traceback.format_exc()
        print("[EXCEPTION]", tb)
        return JSONResponse({"success": False, "error": str(exc), "traceback": tb}, status_code=500)


SAVE_DIR = r"E:\projects\myproject\project_2025_10_21\OCR_server\downloaded\OCR_output_image"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.post("/save_text")
async def save_text(data: dict = Body(...)):
    filename = data.get("filename", "output.txt")
    content = data.get("content", "")
    save_path = os.path.join(SAVE_DIR, filename)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[ Saved] {save_path}")
    return {"status": "ok", "saved_path": save_path}
# ---------- 啟動伺服器 ----------
if __name__ == "__main__":
    uvicorn.run(app, host="192.168.3.220", port=8000)
