import os
import pymysql
import pymysql.cursors

# 🟢 智慧型主機判定：
# 如果是在 Docker 貨櫃裡，會去讀取我們塞給它的環境變數（等於 'elderly_db'）
# 如果是在 Mac 本地直接執行，讀不到變數，就會自動退回預設的 '127.0.0.1'
db_host = os.getenv("DB_HOST", "127.0.0.1")

# 💡 你的 MySQL 連線資訊
DB_CONFIG = {
    'host': db_host,                  # 🟢 改用智慧型變數！自動辨識 Docker 內外
    'user': 'root',
    'password': 'P@ssw0rd',           # 你的 MySQL 密碼
    'database': 'elderly_safety_db',  # 剛剛在 Workbench 建立的資料庫
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """建立並回傳資料庫連線"""
    return pymysql.connect(**DB_CONFIG)

def init_db():
    """初始化資料庫：建立長輩表與警報紀錄表，並自動預塞測試資料"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1. 建立長輩基本資料表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    room_number VARCHAR(20) NOT NULL,
                    line_token VARCHAR(255) NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 2. 建立異常警報紀錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fall_alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    elder_id INT NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    snapshot_url VARCHAR(255) NULL,
                    status VARCHAR(20) DEFAULT 'unhandled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (elder_id) REFERENCES elders(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 3. 🤖 自動預塞測試長輩資料 (id=99)，避免 AI 測試時觸發外鍵約束衝突
            cursor.execute("""
                INSERT INTO elders (id, name, room_number, line_token) 
                VALUES (99, '王大爺', 'A-301', 'MOCK_LINE_TOKEN_12345')
                ON DUPLICATE KEY UPDATE name='王大爺';
            """)
            
        connection.commit()
        print("🗄️ MySQL 資料表初始化與測試長者資料預塞成功！")
    except Exception as e:
        print(f"❌ 資料表建立失敗: {e}")
    finally:
        connection.close()

def save_alert_to_db(elder_id: int, alert_type: str, snapshot_url: str = None):
    """將 AI 觸發的警報寫入資料庫"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO fall_alerts (elder_id, alert_type, snapshot_url) VALUES (%s, %s, %s)"
            cursor.execute(sql, (elder_id, alert_type, snapshot_url))
        connection.commit()
        print(f"💾 警報成功寫入 MySQL！(長輩 ID: {elder_id})")
    except Exception as e:
        print(f"❌ 寫入資料庫失敗: {e}")
        raise e
    finally:
        connection.close()

def get_elder_line_token(elder_id: int):
    """查詢特定長輩的 Line Notify Token"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT line_token FROM elders WHERE id = %s"
            cursor.execute(sql, (elder_id,))
            result = cursor.fetchone()
            return result['line_token'] if result else None
    except Exception as e:
        print(f"❌ 查詢 Token 失敗: {e}")
        return None
    finally:
        connection.close()