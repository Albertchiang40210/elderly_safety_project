import streamlit as st
import streamlit.components.v1 as components  # 🏆 核心修正：導入官方 HTML 元件沙盒支援
import requests
import pandas as pd
import qrcode
import time
from io import BytesIO

st.set_page_config(page_title="安養中心AI智慧照護系統管理中心", layout="wide")

# =========================================================================
# 🌐 拓撲網路層定義（🏆 終極優化：手機走外網 ngrok，電腦網頁走本機 Localhost）
# =========================================================================
# 📱 手機端：因為在外面，維持走外網 ngrok 機制
NGROK_BASE_URL = "https://uncrown-pacific-sprout.ngrok-free.dev"
CAMERA_URL = f"{NGROK_BASE_URL}/mobile-camera"

# 💻 電腦護理站端：因為跟後端在同一台 Mac，直接走本機，100% 免疫 ngrok 警告與卡死
LOCAL_BASE_URL = "http://127.0.0.1:8000"
BACKEND_URL = f"{LOCAL_BASE_URL}/api/v1/alerts"
WS_BASE_URL = "ws://127.0.0.1:8000"


# =========================================================================
# 🎨 注入日系溫馨居家風格 CSS 樣式
# =========================================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #faf8f5;
        color: #4a4641;
    }
    h1 {
        font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif;
        font-weight: 700;
        color: #3d5245;
        padding-bottom: 5px;
    }
    div[data-testid="stMetricCustomComponent"] {
        background-color: #ffffff !important;
        border: 1px solid #eaddcf !important;
        border-radius: 16px !important;
        padding: 18px 24px !important;
        box-shadow: 0 6px 16px rgba(165, 145, 125, 0.06) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="stMetricCustomComponent"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(165, 145, 125, 0.12) !important;
        border-color: #c9b09a !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #f2ede4 !important;
        border-right: 1px solid #e3dacd;
    }
    div[data-border="true"] {
        border: 1px solid #eaddcf !important;
        border-radius: 16px !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 18px rgba(165, 145, 125, 0.05) !important;
    }
    .home-danger-box {
        background: linear-gradient(90deg, #fff3f0 0%, #fffdfc 100%);
        border-left: 6px solid #ff7b6b;
        border-top: 1px solid #ffe3de;
        border-bottom: 1px solid #ffe3de;
        border-right: 1px solid #ffe3de;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(255, 123, 107, 0.08);
    }
    .stButton>button {
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

zone_mapping = {
    1: "一樓溫馨客廳", 
    2: "中央餐廳與走道", 
    3: "101號房", 
    4: "102號房", 
    5: "103號房",
    6: "公共洗澡區"
}

# =========================================================================
# 🔄 數據核心層
# =========================================================================
try:
    response = requests.get(BACKEND_URL, timeout=2)
    if response.status_code == 200:
        data = response.json()
        if not isinstance(data, list): data = []
    else: data = []
except Exception as e:
    data = []

if data:
    df = pd.DataFrame(data)
    df = df.rename(columns={
        "id": "事件 ID",
        "zone_name": "發生區域",  
        "alert_type": "事件類型",
        "timestamp": "通報時間",
        "status": "安全狀態"      
    })
    df = df[["事件 ID", "發生區域", "事件類型", "通報時間", "安全狀態"]]
    df["事件類型"] = df["事件類型"].replace({"fall": "🤸 偵測到跌倒", "SOS": "🚨 緊急求助"})
else:
    df = pd.DataFrame(columns=["事件 ID", "發生區域", "事件類型", "通報時間", "安全狀態"])

unhandled_count = len(df[df["安全狀態"] == "未處理"]) if not df.empty else 0
total_count = len(df) if not df.empty else 0


# =========================================================================
# 🛠️ 側邊欄佈局
# =========================================================================
st.sidebar.markdown("<h2 style='color:#3d5245; font-size:20px; font-weight:700;'>🎨 模擬安養中心監視器</h2>", unsafe_allow_html=True)

st.sidebar.subheader("📱 鏡頭配對QRcode")

@st.cache_data(show_spinner=False)
def generate_static_qrcode(url):
    qr_core = qrcode.QRCode(
        version=2,                                          
        error_correction=qrcode.constants.ERROR_CORRECT_M, 
        box_size=10,                                        
        border=3                                            
    )
    qr_core.add_data(url)
    qr_core.make(fit=True)
    qr_img = qr_core.make_image(fill_color="#2b2b2b", back_color="white") 
    
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    return qr_buf.getvalue()

qrcode_bytes = generate_static_qrcode(CAMERA_URL)

if qrcode_bytes:
    st.sidebar.image(qrcode_bytes, caption="手機掃描立即連線", width=180)
else:
    st.sidebar.caption("⚠️ 配對條碼模組加載異常")

# 模擬跌倒測試區
st.sidebar.markdown("<hr style='border-color:#e3dacd; margin: 10px 0;'/>", unsafe_allow_html=True)
st.sidebar.subheader("🧪 系統功能自我檢測")

test_zone = st.sidebar.selectbox(
    "選擇欲模擬的測試房間：",
    options=[1, 2, 3, 4, 5, 6],
    format_func=lambda x: {
        1: "🛋️ 一樓溫馨客廳",
        2: "🍽️ 中央餐廳與走道",
        3: "🛏️ 101號房",
        4: "🛏️ 102號房",
        5: "🛏️ 103號房",
        6: "🛀 公共洗澡區"
    }[x],
    key="test_zone_select"
)

if st.sidebar.button("💥 觸發模擬跌倒事件", type="secondary", use_container_width=True):
    try:
        payload = {"camera_id": test_zone, "alert_type": "fall"}
        test_res = requests.post(BACKEND_URL, json=payload, timeout=3)
        
        if test_res.status_code == 200:
            res_json = test_res.json()
            if res_json.get("status") == "ignored":
                st.sidebar.warning("🛑 該房間目前已有未處理警報，因防洪鎖機制，本次模擬已被自動攔截。")
            else:
                st.toast("🚀 模擬訊號已送出！資料庫已寫入，LINE 訊息即時通報中！", icon="🔔")
                time.sleep(0.5)
                st.rerun()
        else:
            st.sidebar.error(f"連線失敗，錯誤碼：{test_res.status_code}")
    except Exception as e:
        st.sidebar.error(f"連線後端發生異常: {e}")

st.sidebar.markdown("<hr style='border-color:#e3dacd; margin: 10px 0;'/>", unsafe_allow_html=True)

# 安全解除面板
st.sidebar.subheader("🔒 安全狀態解除")
if unhandled_count > 0:
    unhandled_options = df[df["安全狀態"] == "未處理"]
    unhandled_list = [f"{row['事件 ID']} 號 — 【{row['發生區域']}】" for _, row in unhandled_options.iterrows()]
    
    selected_option = st.sidebar.selectbox("選取已確認安全的區域：", options=unhandled_list)
    selected_id = int(selected_option.split(" 號")[0])
    
    if st.sidebar.button("✔️ 已確認安全（解除警報）", type="primary", use_container_width=True):
        try:
            resolve_url = f"{LOCAL_BASE_URL}/api/v1/alerts/{selected_id}/resolve"
            res = requests.put(resolve_url, timeout=2)
            if res.status_code == 200:
                st.toast(f"🎉 事件 {selected_id} 號區域狀態已確認安全！", icon="✅")
                time.sleep(0.5)
                st.rerun()
            else:
                st.sidebar.error(f"解除失敗：{res.text}")
        except Exception as e:
            st.sidebar.error(f"連線錯誤：{e}")
else:
    st.sidebar.success("🟢 長者目前平安無事")


# =========================================================================
# 🖥️ 主畫面佈局
# =========================================================================
st.title("🏥 護理站安全風險監護中心")
st.caption("資展國際 第三組期末專題研發雛形 (YOLOv8-Pose + 邊緣端去識別化運算)")

col1, col2, col3 = st.columns([1, 1, 2])
col1.metric(label="機構至今異常累計", value=f"{total_count} 次")
col2.metric(label="🚨 未確認緊急事件", value=f"{unhandled_count} 筆")
with col3:
    st.write("")
    if st.button("🔄 手動重新刷新", use_container_width=True):
        st.rerun()

if unhandled_count > 0:
    st.markdown(f"""
        <div class="home-danger-box">
            <h4 style="margin:0; color:#d94536; font-weight:bold; font-size:16px;">💡 【系統緊急通知】</h4>
            <p style="margin:6px 0 0 0; color:#5c4742; font-size:14px;">
                遠端系統偵測到機構區域正發生 <b>{unhandled_count} 筆</b> 跌倒意外！請立刻切換下方即時動態查看長者狀況。
            </p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

# 🎬 核心 4 : 4 雙欄佈局
video_col, info_col = st.columns([4, 4])

with video_col:
    st.markdown("<h3 style='color:#3d5245; font-size:16px; font-weight:700;'>📹 遠端關懷區域即時動態</h3>", unsafe_allow_html=True)
    selected_cam = st.selectbox(
        "🖥️ 切換目前要關懷的機構區域：",
        options=[1, 2, 3, 4, 5, 6],
        format_func=lambda x: {
            1: "🛋️ 鏡頭 1 號通道 (一樓溫馨客廳)",
            2: "🍽️ 鏡頭 2 號通道 (中央餐廳與走道)",
            3: "🛏️ 鏡頭 3 號通道 (101號房)",
            4: "🛏️ 鏡頭 4 號通道 (102號房)",
            5: "🛏️ 鏡頭 5 號通道 (103號房)",
            6: "🛀 鏡頭 6 號通道 (公共洗澡區)"
        }[x]
    )

    # 🎯 本地端高速解碼畫布
    video_container = st.container(border=True)
    with video_container:
        # 🌟 核心改動：走本機 ws 協定，秒速通關！
        ws_stream_endpoint = f"{WS_BASE_URL}/api/v1/stream/{selected_cam}/ws"
        
        html_layout = f"""<div style="text-align: center; margin: 5px 0;">
<div style="margin: 0 auto; max-width: 100%; width: 480px; height: 270px; border-radius: 12px; overflow: hidden; background-color: #2b2b2b; box-shadow: 0 4px 12px rgba(0,0,0,0.1); position: relative;">
<canvas id="liveCanvas" style="width: 100%; height: 100%; object-fit: contain;"></canvas>
<div id="loadingText" style="position: absolute; top: 40%; left: 0; width: 100%; color: #eaddcf; font-size: 14px; font-weight: bold;">
📡 正在接收地端 AI 骨架影像數據...
</div>
</div>
<p style="color: #3d5245; font-size: 13px; margin-top: 10px; font-weight: bold;">🌍 遠端外網 WebSocket 高速去識別化分析中</p>

<script>
(function() {{
    const canvas = document.getElementById('liveCanvas');
    const ctx = canvas.getContext('2d');
    const loading = document.getElementById('loadingText');
    let ws = new WebSocket("{ws_stream_endpoint}");
    
    ws.onmessage = function(event) {{
        loading.style.display = 'none';
        const img = new Image();
        img.onload = function() {{
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
        }};
        img.src = "data:image/jpeg;base64," + event.data;
    }};
    ws.onclose = function() {{
        loading.style.display = 'block';
        loading.innerText = "❌ 遠端串流已離線，等待機構系統點火...";
    }};
}})();
</script>
</div>"""
        
        # 🏆 終極修正：改用 components.html 讓 WebSocket 有獨立沙盒生命週期
        # 彻底阻斷 Streamlit Rerun 造成的多重重連、卡死與畫面黑屏問題！
        components.html(html_layout, height=330)

with info_col:
    st.markdown("<h3 style='color:#3d5245; font-size:16px; font-weight:700;'>ℹ️ 機構中心應變資訊</h3>", unsafe_allow_html=True)
    st.info(f"📍 **當前觀看區域：** {zone_mapping[selected_cam]}")
    
    with st.expander("🚨 機構跌倒緊急應變指引 (SOP)", expanded=True):
        st.markdown(
            "1. 確認畫面上骨架狀態：檢視長者是否正處於倒地無法起身姿勢。\n\n"
            "2. 優先透過該區域廣播系統、床頭對講機呼叫，或指派就近護理人員現場確認。\n\n"
            "3. 請立刻通報值班護理長、機構負責人，並同步聯絡特約醫院或撥打 119。\n\n"
            "4. 緊急狀態解除後請護理人員於系統控制面板點擊「解除警報」，並確實填寫異常事件紀錄表。"
        )
        
    with st.container(border=True):
        st.markdown("<h4 style='color:#3d5245; margin-top:0;'>🔒 邊緣運算與隱私尊嚴保護</h4>", unsafe_allow_html=True)
        st.caption(
            "本守護系統採用 **Edge AI（地端邊緣運算）** 技術。長者在房間內的真實彩色影像「**完全不上傳雲端資料庫**」，"
            "僅在地端主機進行去識別化的骨架關節點分析。家屬端與 MySQL 僅同步事件代碼，完美捍衛長者隱私尊嚴。"
        )

st.markdown("---")

# 📋 底部歷史事件表格
st.markdown("<h3 style='color:#3d5245; font-size:16px; font-weight:700;'>📋 歷史安全日誌看板 (資料庫多表即時同步)</h3>", unsafe_allow_html=True)
if not df.empty and total_count > 0:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("目前各區域運作正常，無任何安全異常日誌。")