from ultralytics import YOLO

def main():
    # 🎯 採用 s (Small) 等級，既能防過擬合，其腦容量又足以應付 102 個關鍵點
    model = YOLO('yolov8s-pose.pt')

    print("⚡ 90張精實資料集戰術啟動！即將在 30 秒內結束戰鬥...")

    model.train(
        data='data.yaml',       
        epochs=100,             # 跑 100 輪，反正只要 20 秒，讓它反覆看熟
        imgsz=640,              # 堅持 640 解析度，確保 102 個點不會糊掉
        batch=8,                # 小 batch 適合小資料集，細細修正盲點
        device='mps',           # 讓 M5 Pro 瞬間爆發
        workers=4,              
        
        # 🎯 救命稻草：強效資料增強（讓 90 張照片在 AI 眼裡變成無限可能）
        augment=True,           
        degrees=15.0,           # 旋轉正負 15 度
        scale=0.5,              # 隨機縮放
        fliplr=0.5,             # 左右翻轉
        
        project='elderly_safety', 
        name='yolov8s_90pics_run', 
        save=True,              
        val=True,               
    )

if __name__ == '__main__':
    main()