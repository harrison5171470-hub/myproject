# 匯入所需模組
import json
import os
import tkinter as tk
import pyperclip
from datetime import datetime

# 資料存到 %APPDATA%\ClipboardManager，確保任何使用者都有寫入權限
APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ClipboardManager")
os.makedirs(APP_DIR, exist_ok=True)
DATA_FILE = os.path.join(APP_DIR, "clipboard_history.json")

# 最多保留的歷史筆數
MAX_HISTORY = 500

# 全域變數：所有剪貼記錄（以文字內容為 key）、日期群組展開狀態、上次剪貼板內容
entries_by_text = {}
group_state = {}
last_clipboard = None

# 日期群組的 UI 元件參考
date_groups = {}


# 將 datetime 物件格式化為可讀字串
def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# 從 JSON 檔案載入歷史記錄到 entries_by_text
def load_data():
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return
        data = json.loads(raw)
        if not isinstance(data, list):
            return
        for item in data:
            text = item.get("text")
            time_str = item.get("time")
            if not text or not time_str:
                continue
            try:
                entries_by_text[text] = {
                    "text": text,
                    "time": datetime.fromisoformat(time_str),
                }
            except ValueError:
                # 時間格式異常則跳過該筆
                continue
    except (json.JSONDecodeError, OSError) as e:
        # 檔案損壞時先備份，再印出警告
        backup = DATA_FILE + ".bak"
        try:
            import shutil
            shutil.copy2(DATA_FILE, backup)
        except Exception:
            pass
        print(f"[警告] 讀取歷史失敗，已備份至 {backup}。錯誤：{e}")


# 將 entries_by_text 存回 JSON 檔案，只保留最新 MAX_HISTORY 筆
def save_data():
    sorted_entries = sorted(entries_by_text.values(), key=lambda x: x["time"], reverse=True)
    data = [
        {
            "text": entry["text"],
            "time": entry["time"].isoformat(),
        }
        for entry in sorted_entries[:MAX_HISTORY]
    ]
    # 先寫暫存檔，完成後再替換，避免寫到一半導致 JSON 損壞
    tmp_file = DATA_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, DATA_FILE)


# 切換某日期群組的展開／收合狀態
def toggle_group(date_key):
    state = group_state.get(date_key, False)
    group_state[date_key] = not state
    container = date_groups[date_key]["container"]
    button = date_groups[date_key]["button"]
    if state:
        container.forget()
        button.configure(text="▶")
    else:
        container.pack(fill="x", padx=10, pady=(0, 6))
        button.configure(text="▼")


# 刪除指定文字的歷史記錄並更新畫面
def delete_entry(text):
    if text in entries_by_text:
        del entries_by_text[text]
        save_data()
        rebuild_ui()


# 將指定文字複製到剪貼板，並更新該筆的最後使用時間
def copy_text(text):
    pyperclip.copy(text)
    now = datetime.now()
    if text in entries_by_text:
        entries_by_text[text]["time"] = now
        save_data()
        rebuild_ui()


# 新增或更新一筆剪貼記錄，若文字已存在則只更新時間
def add_or_update_entry(text, timestamp=None):
    now = timestamp or datetime.now()
    if not text:
        return
    if text in entries_by_text:
        entries_by_text[text]["time"] = now
    else:
        entries_by_text[text] = {"text": text, "time": now}
    save_data()
    rebuild_ui()


# 重新繪製整個歷史列表（依日期分群，支援關鍵字篩選）
def rebuild_ui():
    # 清除舊有的 UI 元件
    for child in scrollable_frame.winfo_children():
        child.destroy()

    # 依搜尋關鍵字篩選並按日期分群
    grouped = {}
    keyword = search_var.get().strip().lower()
    for entry in sorted(entries_by_text.values(), key=lambda x: x["time"], reverse=True):
        if keyword and keyword not in entry["text"].lower():
            continue
        date_key = entry["time"].date().isoformat()
        grouped.setdefault(date_key, []).append(entry)

    # 若無資料則顯示提示文字
    if not grouped:
        empty_label = tk.Label(scrollable_frame, text="沒有符合搜尋的結果。" if keyword else "目前沒有剪貼紀錄。", bg="#ffffff", fg="#888888")
        empty_label.pack(padx=10, pady=10)
        return

    # 依日期由新到舊建立群組標題與內容
    for date_key in sorted(grouped.keys(), reverse=True):
        items = grouped[date_key]
        if date_key not in group_state:
            group_state[date_key] = False

        # 群組標題列（含展開／收合按鈕與筆數）
        header_frame = tk.Frame(scrollable_frame, bg="#ececec", bd=1, relief="solid")
        header_frame.pack(fill="x", pady=(6, 0))

        should_expand = group_state[date_key] or bool(keyword)
        button = tk.Button(
            header_frame,
            text="▼" if should_expand else "▶",
            width=2,
            relief="flat",
            command=lambda d=date_key: toggle_group(d),
        )
        button.pack(side="left", padx=4, pady=4)

        info_text = f"{date_key}  ({len(items)} 筆)"
        header_label = tk.Label(header_frame, text=info_text, font=(None, 10, "bold"), bg="#ececec")
        header_label.pack(side="left", padx=8)

        # 群組內容容器（展開時才顯示）
        container = tk.Frame(scrollable_frame, bg="#f9f9f9")
        if should_expand:
            container.pack(fill="x", padx=10, pady=(0, 6))

        date_groups[date_key] = {
            "container": container,
            "button": button,
        }

        # 逐筆建立記錄列（時間、文字、複製按鈕、刪除按鈕）
        for entry in items:
            entry_frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
            entry_frame.pack(fill="x", pady=3, padx=8)

            time_label = tk.Label(
                entry_frame,
                text=format_time(entry["time"]),
                width=20,
                anchor="w",
                bg="#ffffff",
                fg="#333333",
            )
            time_label.pack(side="left", padx=6, pady=6)

            text_label = tk.Label(
                entry_frame,
                text=entry["text"],
                anchor="w",
                justify="left",
                wraplength=350,
                bg="#ffffff",
            )
            text_label.pack(side="left", fill="x", expand=True, padx=6, pady=6)

            delete_button = tk.Button(
                entry_frame,
                text="刪除",
                width=6,
                fg="#cc0000",
                command=lambda t=entry["text"]: delete_entry(t),
            )
            delete_button.pack(side="right", padx=(0, 6), pady=6)

            copy_button = tk.Button(
                entry_frame,
                text="複製",
                width=8,
                command=lambda t=entry["text"]: copy_text(t),
            )
            copy_button.pack(side="right", padx=6, pady=6)


# 每秒輪詢剪貼板，若內容有變化則自動新增記錄
def poll_clipboard():
    global last_clipboard
    try:
        new_text = pyperclip.paste()
    except Exception:
        new_text = None

    if new_text and new_text != last_clipboard:
        last_clipboard = new_text
        add_or_update_entry(new_text)
    root.after(1000, poll_clipboard)


# 建立主視窗
root = tk.Tk()
root.title("Clipboard Manager")
root.geometry("760x520")
root.configure(bg="#f0f0f0")

# 搜尋欄位的綁定變數
search_var = tk.StringVar()

# 頂部標題與搜尋列
header_frame = tk.Frame(root, bg="#f0f0f0")
header_frame.pack(fill="x", padx=12, pady=10)

title_label = tk.Label(header_frame, text="剪貼簿歷史", font=(None, 14, "bold"), bg="#f0f0f0")
title_label.pack(side="left")

search_frame = tk.Frame(header_frame, bg="#f0f0f0")
search_frame.pack(side="right")

search_label = tk.Label(search_frame, text="搜尋：", bg="#f0f0f0")
search_label.pack(side="left", padx=(0, 4))

search_entry = tk.Entry(search_frame, textvariable=search_var, width=24)
search_entry.pack(side="left", padx=(0, 4))
search_entry.bind("<Return>", lambda event: rebuild_ui())

search_button = tk.Button(search_frame, text="搜尋", command=rebuild_ui)
search_button.pack(side="left", padx=(0, 4))

clear_button = tk.Button(search_frame, text="清除", command=lambda: (search_var.set(""), rebuild_ui()))
clear_button.pack(side="left")

# 可捲動的列表區域
container = tk.Frame(root, bg="#f0f0f0")
container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

canvas = tk.Canvas(container, bg="#ffffff", highlightthickness=0)
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")
canvas.pack(side=tk.LEFT, fill="both", expand=True)
canvas.configure(yscrollcommand=scrollbar.set)

scrollable_frame = tk.Frame(canvas, bg="#ffffff")
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")


# 當內容改變時更新捲動範圍
def configure_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", configure_scroll_region)

# 啟動：載入歷史 → 初始化剪貼板基準值（避免啟動時誤觸發存檔）→ 顯示畫面 → 開始輪詢
load_data()
try:
    last_clipboard = pyperclip.paste()
except Exception:
    last_clipboard = None
rebuild_ui()
root.after(1000, poll_clipboard)
root.mainloop()
