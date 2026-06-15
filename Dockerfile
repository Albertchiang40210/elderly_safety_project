# 1. 改用官方 Python 輕量基底（支援 Mac ARM64 晶片）
FROM python:3.10-slim

# 2. 設定貨櫃內的工作目錄
WORKDIR /app

# 3. 安裝 Linux 基礎套件（一網打盡 OpenCV 與 YOLO 核心零件）
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxcb1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製 Python 套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製目前資料夾下的所有程式碼與 YOLO 模型資料進貨櫃
COPY . .

# 6. 開放 FastAPI 的 8000 埠口
EXPOSE 8000

# 7. 啟動服務（因為 main.py 在 backend 資料夾內，所以是 backend.main:app）
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]