# 👵 銀髮長者安全監控與 AI 影像辨識系統 (Elderly Safety Project)

[![Docker Build](https://img.shields.io/badge/Docker-Containerization-blue?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit)](https://streamlit.io/)

本系統是一款專為銀髮族長者設計的地端自動化安全監控儀。採用前後端分離的微服務架構 (Microservices Architecture)，前端透過 Streamlit 打造即時監控戰情室，後端基於 FastAPI 高併發框架並動態調用 YOLOv8 姿態/物件偵測模型，實現低延遲、高精準度的長者行為與環境安全檢測，並將事件日誌結構化留存於地端資料庫。

---

## 🚀 系統核心架構 (System Architecture)

本系統全面導入 Docker 容器化技術，將服務解耦為兩大核心模組，兼具高容錯率與產線彈性擴充性：

*   **前端視覺化監控戰情室 (`frontend_app.py`)**
    *   基於 Streamlit 打造工業級深色模式 (Dark Mode) 監控面板。
    *   整合三大核心指標數據卡 (KPI Cards)：即時異常告警、當日事件統計、系統推理延遲。
    *   內建即時串流影像回顯面板與結構化 SQL 資料庫同步日誌看板。
*   **後端 AI 推理核心 (`ai_core/`)**
    *   基於 FastAPI 建立高併發 API，負責影像串流接收、解碼與預處理。
    *   動態調用核心 AI 大腦（經精密特徵訓練之 `yolov8s-pose.pt` 模型），即時解析長者姿態。
*   **地端數據安全留存 (Data Storage)**
    *   採用 MySQL 關係型資料庫，透過事件資料表自動審計每筆辨識紀錄（包含：時間戳記、異常類別、信心度得分、警報狀態）。

---

## 🛠️ 技術痛點優化與底層修復 (Logic Optimization)

1.  **跨容器連線網路隔離壁壘導正 (Networking)**
    *   **痛點：** 容器內的後端 API 若設定 `127.0.0.1`，會嘗試在容器內部迴路尋找資料庫，導致連線被壁壘阻斷，無法連回 Mac 本地端的 MySQL。
    *   **解法：** 調整資料庫連線字串，利用 Docker 專屬虛擬網域 `host.docker.internal` 成功突破容器隔離壁壘，實現地端數據穩穩寫入。
2.  **Linux 底層影像庫相容性修復 (OpenCV Dependency)**
    *   **痛點：** 新版 Debian (Bookworm) 系統中，舊版影像相依庫已被官方移除，導致 Docker 編譯時拋出 `exit code: 100` 錯誤。
    *   **解法：** 將 Dockerfile 中的 `libgl1-mesa-glx` 導正更名為新版 `libgl1` 與 `libglib2.0-0`，順利通過環境建置。
3.  **微服務標準化群組路由**
    *   **優化：** 全面捨棄單兵作戰容器，導入 `docker-compose` 標準化多容器編排架構。前後端容器透過 Docker 內部隱形局域網網域（`http://coffee_backend:8000`）進行高效安全通訊。

---

## 📦 快速開始與容器建置 (Quick Start)

本專案已完全脫離環境依賴，不需在本地安裝 Python、OpenCV 或模型相依庫，僅需透過以下指令即可實現秒級自動化建置與開機：

### 1. 複製專案並進入資料夾
git clone [https://github.com/Albertchiang40210/elderly_safety_project.git](https://github.com/Albertchiang40210/elderly_safety_project.git)
cd elderly_safety_project
2. 微服務一鍵點火啟動 (Docker Compose)
使用 Docker Compose 在背景同時拉起前端、後端與網路關聯：
Bash
docker compose up -d --build
3. 訪問系統驗收
打開瀏覽器，輸入以下網址即可直接進入長者安全監控戰情室：
前端視覺化面板： http://localhost:8501
後端 FastAPI 交互式 API 文件： http://localhost:8000/docs
🗂️ 專案目錄結構 (Project Structure)
Plaintext
elderly_safety_project/
├── ai_core/               # 後端 AI 推理核心模組
│   ├── database.py        # 資料庫連線與寫入邏輯
│   ├── detector.py        # YOLOv8 模型推理核心
│   └── main.py            # FastAPI 主程式
├── dataset/               # 訓練與驗證影像數據集
├── frontend_app.py        # Streamlit 前端戰情室網頁
├── docker-compose.yml     # 標準化微服務多容器編排設定檔
├── Dockerfile             # 輕量化基礎底圖建置藍圖
├── requirements.txt       # 專案相依套件清單
├── start_project.sh       # 地端備用一鍵雙開啟動腳本
└── .gitignore             # Git 雲端同步過濾設定檔
