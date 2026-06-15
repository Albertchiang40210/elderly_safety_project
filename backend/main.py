import base64
import numpy as np
import cv2
import asyncio
import time
import requests  # 📢 用於發送 HTTP POST 請求給 LINE 廣播伺服器
# 🏆 核心修正：正式導入 Body 用於高效讀取同步二進位流
from fastapi import FastAPI, HTTPException, WebSocket, Response, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# 匯入基礎資料庫連線機制（確保底層使用 elderly_safety_db）
from backend.database import init_db, get_db_connection

# 🏢 調整為安養中心專屬系統名稱
app = FastAPI(title="安養中心AI智慧照護系統 — 中央中樞 API")

# 啟用全網域 CORS 跨存取權限，確保遠端手機與 Streamlit 連線暢通
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

class AlertCreate(BaseModel):
    camera_id: int
    alert_type: str = "fall"
    snapshot_url: Optional[str] = None

# 全域多軌影像中轉緩衝字典（支援 1~6 號獨立機構空間通道 🚀）
latest_video_frames = {}       
latest_processed_frames = {}   

# 🔄 Frontend 刷新監聽旗標（每次有新跌倒警報，這個數字就會 +1）
alert_update_counter = 0

# 🏥 空間名稱對照表（🏆 完美對齊 MySQL 與 Streamlit 前端，擴充至 6 號通道）
ZONE_MAPPING = {
    1: "一樓溫馨客廳",
    2: "中央餐廳與走道",
    3: "101號房",
    4: "102號房",
    5: "103號房",
    6: "公共洗澡區"
}

# =========================================================================
# 📢 LINE Messaging API - Broadcast (廣播群發) 核心大絕招
# =========================================================================
def send_home_line_message_v2(zone_name: str):
    """
    完全不需要任何 User ID 或 Group ID！
    只要有加這個官方帳號好友的人，通通會在同一秒各自收到一對一緊急通知！
    """
    line_broadcast_url = "https://api.line.me/v2/bot/message/broadcast"
    
    LINE_CHANNEL_ACCESS_TOKEN = "2O08JRu5jKGBwxvR9ly3Ocurc7peZs7wu7oG1cI4ONGxatInNGuk4DA5HNR7XYFTzTaY7jP0ahxYYbg8M/VpMaodGxnAUWbVO1PXgksglK7VZVQ5FId0JO2hjdvY2yKsa7efd+DISntZJd6QF6kIRQdB04t89/1O/w1cDnyilFU="

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    # 🏢 調整為安養機構專業通報語氣
    alert_text = (
        f"🏥【安養機構安全緊急通報】\n\n"
        f"遠端系統即時偵測到機構區域『{zone_name}』疑似發生跌倒異常！\n\n"
        f"📌 請值班護理人員/照服員立刻確認現場畫面與長者動態：\n"
        f"https://uncrown-pacific-sprout.ngrok-free.dev"
    )
    
    payload = {
        "messages": [
            {
                "type": "text",
                "text": alert_text
            }
        ]
    }
    
    try:
        res = requests.post(line_broadcast_url, headers=headers, json=payload, timeout=4)
        if res.status_code == 200:
            print(f"📢 [Broadcast] 成功向所有照護人員發送安全通報！場域：{zone_name}")
        else:
            print(f"❌ 廣播失敗，狀態碼：{res.status_code}，錯誤細節：{res.text}")
    except Exception as e:
        print(f"❌ 連線至 LINE 廣播伺服器時發生異常: {e}")


# ----------------- 📱 機構端手機 CCTV 空間多路傳輸端 -----------------

@app.get("/mobile-camera", response_class=HTMLResponse)
def get_mobile_camera_page():
    """模擬護理人員或角落架設的舊手機，掃碼即刻變身機構守護鏡頭"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>安養機構AI智慧守護鏡頭端</title>
        <style>
            body { margin: 0; background: #111; text-align: center; color: white; font-family: sans-serif; }
            #status { padding: 15px; background: #ff9900; font-weight: bold; font-size: 16px; transition: 0.3s; }
            .control-panel { padding: 15px; background: #222; margin-bottom: 10px; }
            select { padding: 10px; font-size: 16px; width: 80%; max-width: 300px; border-radius: 5px; border: none; }
            video { width: 100%; max-width: 480px; border-radius: 8px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div id="status">📡 正在辨識機構防護空間...</div>
        <div class="control-panel">
            <label style="display:block; margin-bottom: 8px; font-size: 14px; color: #aaa;">此裝置目前的擺放區域：</label>
            <select id="cameraSelect">
                <option value="1">🛋️ 擺放在：一樓溫馨客廳</option>
                <option value="2">🍽️ 擺放在：中央餐廳與走道</option>
                <option value="3">🛏️ 擺放在：101號房</option>
                <option value="4">🛏️ 擺放在：102號房</option>
                <option value="5">🛏️ 擺放在：103號房</option>
                <option value="6">🛀 擺放在：公共洗澡區</option>
            </select>
        </div>
        <video id="video" autoplay playsinline></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusDiv = document.getElementById('status');
            const cameraSelect = document.getElementById('cameraSelect');
            let ws = null; let streamInterval = null;

            function startStreaming(cameraId) {
                if (ws) ws.close();
                const wsProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
                ws = new WebSocket(wsProtocol + location.host + '/ws/camera/' + cameraId);
                ws.onopen = () => { 
                    const zoneInfo = cameraSelect.options[cameraSelect.selectedIndex].text;
                    statusDiv.innerText = "🟢 " + zoneInfo + " 守護中 (特徵分析不上雲端)"; 
                    statusDiv.style.background = "#00cc66"; 
                };
                ws.onclose = () => { statusDiv.innerText = "🔴 連線中斷"; statusDiv.style.background = "#ff3333"; };
            }

            cameraSelect.addEventListener('change', (e) => { startStreaming(e.target.value); });
            startStreaming(cameraSelect.value);

            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: 400, height: 300 }, audio: false })
                .then(stream => { video.srcObject = stream; })
                .catch(err => { statusDiv.innerText = "❌ 鏡頭啟動失敗"; });

            video.addEventListener('play', () => {
                canvas.width = 400; canvas.height = 300;
                if (streamInterval) clearInterval(streamInterval);
                streamInterval = setInterval(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        const dataURL = canvas.toDataURL('image/jpeg', 0.5); 
                        ws.send(dataURL);
                    }
                }, 50); 
            });
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/camera/{camera_id}")
async def websocket_camera_endpoint(websocket: WebSocket, camera_id: int):
    global latest_video_frames
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            header, encoded = data.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(img_bytes, np.uint8)
            latest_video_frames[camera_id] = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        pass
    finally:
        if camera_id in latest_video_frames:
            del latest_video_frames[camera_id]

@app.get("/api/v1/get_frame")
def get_frame(camera_id: int = 1):
    global latest_video_frames
    frame = latest_video_frames.get(camera_id)
    if frame is None:
        return Response(status_code=404, content="CCTV Offline")
    _, img_encoded = cv2.imencode('.jpg', frame)
    return Response(content=img_encoded.tobytes(), media_type="image/jpeg")

# ----------------- 🔄 Edge AI 處理後骨架影像中轉 -----------------

@app.post("/api/v1/update_processed_frame/{camera_id}")
def update_processed_frame(camera_id: int, bytes_body: bytes = Body(...)):
    global latest_processed_frames
    latest_processed_frames[camera_id] = bytes_body
    return {"status": "success"}

def mjpeg_frame_generator(camera_id: int):
    global latest_processed_frames
    while True:
        frame = latest_processed_frames.get(camera_id)
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.04) 

@app.get("/api/v1/stream/{camera_id}")
def video_stream_endpoint(camera_id: int):
    return StreamingResponse(mjpeg_frame_generator(camera_id), media_type="multipart/x-mixed-replace; boundary=frame")

# ----------------- 📋 空間事件日誌與解鎖核心 API -----------------

@app.get("/api/v1/alert-check")
def check_alert_update():
    global alert_update_counter
    return {"counter": alert_update_counter}

@app.get("/api/v1/alerts")
def get_alerts():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 💡 這裡底層 JOIN 的是 home_zones，與你剛剛在 MySQL 更新的完全契合！
            sql = """
                SELECT
                    a.id AS id,
                    z.zone_name AS zone_name,
                    a.alert_type AS alert_type,
                    DATE_FORMAT(a.created_at, '%Y-%m-%d %H:%i:%s') AS timestamp,
                    CASE
                        WHEN a.status = 'unhandled' THEN '未處理'
                        ELSE '已處理'
                    END AS status
                FROM fall_alerts a
                LEFT JOIN home_zones z ON a.zone_id = z.id
                ORDER BY a.created_at DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            return JSONResponse(content=results, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.post("/api/v1/alerts")
def create_alert(alert: AlertCreate):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            check_sql = """
                SELECT id FROM fall_alerts 
                WHERE zone_id = %s AND status = 'unhandled' 
                LIMIT 1
            """
            cursor.execute(check_sql, (alert.camera_id,))
            existing_alert = cursor.fetchone()
            
            if existing_alert:
                return JSONResponse(
                    content={"status": "ignored", "message": f"區域 {alert.camera_id} 已有未處理警報，自動防洪攔截"}, 
                    media_type="application/json; charset=utf-8"
                )
            
            insert_sql = "INSERT INTO fall_alerts (zone_id, alert_type, status) VALUES (%s, %s, 'unhandled')"
            cursor.execute(insert_sql, (alert.camera_id, alert.alert_type))
            connection.commit()
            
            current_zone_name = ZONE_MAPPING.get(alert.camera_id, f"未知區域 (鏡頭 {alert.camera_id} 號)")
            send_home_line_message_v2(current_zone_name)
            
            global alert_update_counter
            alert_update_counter += 1
            
        return JSONResponse(content={"status": "success"}, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.put("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE fall_alerts SET status = 'handled' WHERE id = %s"
            cursor.execute(sql, (alert_id,))
            connection.commit()
            
            global alert_update_counter
            alert_update_counter += 1
            
            return JSONResponse(content={"status": "success", "message": f"事件 ID {alert_id} 狀態已成功確認解除"}, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

from fastapi import WebSocketDisconnect

@app.websocket("/api/v1/stream/{camera_id}/ws")
async def video_ws_stream_endpoint(websocket: WebSocket, camera_id: int):
    """【專題發表終極武器】外網通暢無阻的 WebSocket 骨架串流廣播源"""
    await websocket.accept()
    global latest_processed_frames
    last_frame = None
    try:
        while True:
            frame_bytes = latest_processed_frames.get(camera_id)
            if frame_bytes and frame_bytes != last_frame:
                base64_str = base64.b64encode(frame_bytes).decode("utf-8")
                await websocket.send_text(base64_str)
                last_frame = frame_bytes
            await asyncio.sleep(0.04) # 確保 25 FPS 高流暢度且不佔執行緒
    except WebSocketDisconnect:
        print(f"👋 通道 {camera_id} 號的前端遠端 WebSocket 連線已安全中斷。")
    except Exception:
        pass