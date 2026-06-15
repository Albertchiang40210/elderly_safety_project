import cv2
import requests
import numpy as np
import time
import sys
from ultralytics import YOLO

class FallDetector:
    def __init__(self, 
                 model_path='ai_core/weights/best.pt', 
                 backend_url='https://uncrown-pacific-sprout.ngrok-free.dev/api/v1/alerts',
                 frame_url='http://127.0.0.1:8000/api/v1/get_frame',
                 upload_url='http://127.0.0.1:8000/api/v1/update_processed_frame',
                 camera_id: int = 1):
        
        print(f"正在初始化地端 AI 運算核心 (目前指定守護空間通道: {camera_id} 號)...")
        self.model = YOLO(model_path)
        self.backend_url = backend_url
        self.frame_url = frame_url
        self.upload_url = upload_url
        self.camera_id = camera_id
        self.alert_triggered = False  
        self.no_person_count = 0      

    def start_monitoring(self):
        target_frame_url = f"{self.frame_url}?camera_id={self.camera_id}"
        target_upload_url = f"{self.upload_url}/{self.camera_id}"
        
        print(f"📡 [空間通道 {self.camera_id} 號] 安養機構端去識別化防護網已點火啟動... 欲退出請按 Ctrl+C")
        
        while True:
            try:
                response = requests.get(target_frame_url, timeout=1)
                if response.status_code == 200:
                    img_array = np.frombuffer(response.content, dtype=np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                else:
                    time.sleep(0.3)
                    continue
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                continue
            except Exception as e:
                print(f"❌ 邊緣端發生異常: {e}")
                break
            
            # 呼叫 Mac M5 Pro GPU 進行地端骨架推論
            results = self.model(frame, device='mps', verbose=False)
            
            if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
                self.no_person_count = 0  
                kpts = results[0].keypoints.data[0].cpu().numpy() 
                
                try:
                    left_shoulder, right_shoulder = kpts[5], kpts[6]
                    left_hip, right_hip = kpts[11], kpts[12]

                    if all(pt[2] > 0.5 for pt in [left_shoulder, right_shoulder, left_hip, right_hip]):
                        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
                        hip_center_y = (left_hip[1] + right_hip[1]) / 2
                        
                        torso_height = abs(hip_center_y - shoulder_center_y)
                        torso_width = abs(left_shoulder[0] - right_shoulder[0])
                        
                        if torso_height < (torso_width * 0.7):
                            self.trigger_alert()
                        else:
                            if self.alert_triggered:
                                print(f"🔄 [通道 {self.camera_id} 號] 異常姿勢解除，恢復常態守護。")
                                self.alert_triggered = False
                except IndexError:
                    pass
            else:
                self.no_person_count += 1
                if self.no_person_count > 30 and self.alert_triggered:
                    print(f"🔄 [通道 {self.camera_id} 號] 區域恢復空網，解鎖警報鎖。")
                    self.alert_triggered = False
            
            # 將畫有骨架的影像推回後端中轉
            annotated_frame = results[0].plot()
            _, img_encoded = cv2.imencode('.jpg', annotated_frame)
            try:
                requests.post(target_upload_url, data=img_encoded.tobytes(), timeout=0.2)
            except Exception:
                pass

    def trigger_alert(self):
        if not self.alert_triggered:
            print(f"⚠️ [通道 {self.camera_id} 號] 偵測到人體意外跌倒！正在向護理站發送遠端通報...")
            payload = {"camera_id": self.camera_id, "alert_type": "fall"}
            headers = {"ngrok-skip-browser-warning": "true", "Content-Type": "application/json"}
            
            try:
                response = requests.post(self.backend_url, json=payload, headers=headers, timeout=3)
                if response.status_code in [200, 201]:
                    print("✅ 空間安全通報發送成功！")
                    self.alert_triggered = True  
                else:
                    print(f"❌ 遭拒絕，狀態碼: {response.status_code}")
            except Exception as e:
                print(f"❌ 連線失敗: {e}")

if __name__ == "__main__":
    current_cam_id = 1
    if len(sys.argv) > 1:
        try: current_cam_id = int(sys.argv[1])
        except ValueError: pass

    detector = FallDetector(camera_id=current_cam_id)
    try: detector.start_monitoring()  
    except KeyboardInterrupt: print("\n👋 AI 核心已安全關閉。")