# 環境啟動 OCR_server\Scripts\activate
# 有GPU>pip install fastapi uvicorn paddleocr paddlepaddle pillow
# 無GPU>pip install paddlepaddle==2.6.1 -i https://mirror.baidu.com/pypi/simple
# pip install python-multipart

from fastapi import FastAPI, File, UploadFile  # pip install fastapi uvicorn
from paddleocr import PaddleOCR   # pip install paddleocr
from fastapi.responses import JSONResponse
from io import BytesIO  # 內存讀取
from PIL import Image   # pip install pillow
import uvicorn  # pip install uvicorn
import numpy as np  # pip install numpy
import traceback
import cv2  # pip install opencv-python

app = FastAPI()
#ocr = PaddleOCR(use_textline_orientation=True, lang='ch')  # 中英文支援
ocr = PaddleOCR(use_angle_cls=True, lang='ch')  #  啟用角度分類器

@app.post("/upload") # OCR 上傳介面

async def upload(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read() # 讀取上傳的圖檔位元組
        image = Image.open(BytesIO(image_bytes)).convert("RGB") # 轉PIL圖像

        # result>所有圖的辨識結果 list
        result = ocr.ocr(np.array(image))  # 注意：不帶 cls=True

        ocr_boxes = [] # 儲存辨識結果

        #result[0]> 第一張圖辨識結果 dict
        #result[0]['rec_boxes']> 第一張圖所有文字框座標 list
        #zip(result[0]['rec_boxes'], result[0]['rec_texts']) → 把座標陣列和文字配對。
        for box, text in zip(result[0]['rec_boxes'], result[0]['rec_texts']):
            
            # 攤平成一維陣列 array([x0, y0, x1, y1, x2, y2, x3, y3])
            #box = np.array(box).flatten() 
            box = np.array(box)
            print("box:", box, "text:", text)
            if box.ndim == 2 and box.shape[1] == 2:   # shape (4,2)
                xs, ys = box[:,0], box[:,1]
            elif box.ndim == 1 and box.size % 2 == 0: # 一維偶數元素
                box = box.reshape((-1,2))
                xs, ys = box[:,0], box[:,1]
            else:
                continue  # 不合理 box
            x1, y1 = xs.min(), ys.min()  # 左上角
            x2, y2 = xs.max(), ys.max()  # 右下角

            # 取得邊界框左上和右下座標
            # box[:,0] → 所有 x 座標 ，":" 代表選取所有行（也就是 4 個頂點），0 代表選取每行的第 0 個元素（x 座標）
            # box[:,1] → 所有 y 座標 => array([y1, y2, y3, y4])
            #x1, y1 = box[:,0].min(), box[:,1].min()  # 左上角
            #x2, y2 = box[:,0].max(), box[:,1].max()  # 右下角
            
            #x1, y1 = min(box[0],box[2],box[4], box[6]), min(box[1], box[3],box[5],box[7]) # 左上角
            #x2, y2 = max(box[0],box[2],box[4], box[6]), max(box[1], box[3],box[5],box[7]) # 右下角

            ocr_boxes.append({
                "x": int(x1),
                "y": int(y1),
                "w": int(x2 - x1),
                "h": int(y2 - y1),
                "text": text
            })
        print("ocr_boxes:", ocr_boxes)

        response = {
            "success": True, # 辨識成功
            "ocr_engine": "PaddleOCR v5 (textline_orientation)",
            "image_width": image.width,    #圖像寬度
            "image_height": image.height,  #圖像高度
            "ocr_boxes": ocr_boxes  # 辨識文字框列表
        }
        return JSONResponse(response)   # 回傳JSON結果
    except Exception as exc:
        # 回傳 500 並把錯誤內容列出來（方便 client debug）
        tb = traceback.format_exc()
        print("OCR server error:", tb)
        return JSONResponse(
            {"success": False, "error": str(exc), "traceback": tb},
            status_code=500
        )



if __name__ == "__main__": # 直接執行此檔案時啟動伺服器
    # powershell打 ipconfig查IP
    uvicorn.run(app, host="192.168.3.220", port=8000) # 啟動伺服器

