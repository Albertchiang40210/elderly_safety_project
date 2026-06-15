import os
import random
import shutil

def split_existing_train_to_val(dataset_dir, val_ratio=0.2):
    """
    直接把 dataset/images/train 裡面的資料，隨機抽 20% 搬移到 val
    """
    train_img_dir = os.path.join(dataset_dir, 'images', 'train')
    train_lbl_dir = os.path.join(dataset_dir, 'labels', 'train')
    
    val_img_dir = os.path.join(dataset_dir, 'images', 'val')
    val_lbl_dir = os.path.join(dataset_dir, 'labels', 'val')

    # 自動建立 val 資料夾
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)

    # 1. 取得目前 train 裡面所有的圖片檔名（不含副檔名）
    if not os.path.exists(train_img_dir):
        print("❌ 錯誤：找不到 dataset/images/train 資料夾！")
        return
        
    all_files = [os.path.splitext(f)[0] for f in os.listdir(train_img_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.PNG', '.JPG'))]
    total_count = len(all_files)

    if total_count == 0:
        print("❌ 錯誤：目前 train 資料夾裡面沒有任何圖片！")
        return

    # 2. 隨機打亂
    random.seed(42)  # 固定隨機種子，確保切分可複現
    random.shuffle(all_files)

    # 3. 計算 20% 應該要拿多少張
    val_count = int(total_count * val_ratio)
    val_files = all_files[:val_count]

    print(f"📊 目前 Train 資料夾內總計有: {total_count} 筆資料")
    print(f"🚚 正在嚴謹隨機抽取 {val_ratio*100:.0f}% ({val_count} 筆) 移往 Val 驗證集...")

    # 4. 開始執行物理搬移（剪下貼上）
    for file_base in val_files:
        # 偵測圖片真正的副檔名（從截圖看你的主要是 .png）
        img_ext = '.png'
        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG']:
            if os.path.exists(os.path.join(train_img_dir, file_base + ext)):
                img_ext = ext
                break
        
        src_img = os.path.join(train_img_dir, file_base + img_ext)
        dst_img = os.path.join(val_img_dir, file_base + img_ext)
        
        src_lbl = os.path.join(train_lbl_dir, file_base + '.txt')
        dst_lbl = os.path.join(val_lbl_dir, file_base + '.txt')

        # 物理剪下貼上 (shutil.move)
        if os.path.exists(src_img) and os.path.exists(src_lbl):
            shutil.move(src_img, dst_img)
            shutil.move(src_lbl, dst_lbl)

    # 5. 輸出最終成果
    final_train = len(os.listdir(train_img_dir))
    final_val = len(os.listdir(val_img_dir))
    print("\n✅ 80/20 黃金比例切分完成！")
    print(f"   - 最終訓練集 (Train): {final_train} 筆照片 + 標籤")
    print(f"   - 最終驗證集 (Val): {final_val} 筆照片 + 標籤")

if __name__ == "__main__":
    # 指向專案內部的 dataset 資料夾
    TARGET_DATASET = "./dataset"
    split_existing_train_to_val(TARGET_DATASET, val_ratio=0.2)