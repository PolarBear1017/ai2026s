import lpips
import torch
from PIL import Image
import os
import pandas as pd
from skimage.metrics import structural_similarity as ssim
import numpy as np
import torchvision.transforms as transforms
from pathlib import Path

# 初始化 LPIPS 模型（只執行一次）
lpips_model = lpips.LPIPS(net='alex')

def load_and_preprocess_image(image_path, target_size=(224, 224)):
    """ 加載並調整圖片尺寸，確保 LPIPS 比對時圖片尺寸一致 """
    image = Image.open(image_path).convert("RGB")  # 確保是 RGB 圖片
    transform = transforms.Compose([
        transforms.Resize(target_size),  # 重新調整大小
        transforms.ToTensor()
    ])
    return transform(image).unsqueeze(0)  # 增加 batch 維度

def compute_lpips_distance(image1_path, image2_path):
    """ 計算 LPIPS (感知相似度) 距離，確保輸入尺寸一致 """
    image1_tensor = load_and_preprocess_image(image1_path)
    image2_tensor = load_and_preprocess_image(image2_path)

    with torch.no_grad():
        distance = lpips_model.forward(image1_tensor, image2_tensor)

    return distance.item()
def compute_ssim(image1_path, image2_path, target_size=(128, 128)):
    """ 計算 SSIM，優化字體生成專案的準確度 """
    try:
        # 轉為灰階 'L' 以專注於字體結構，並調整大小
        image1 = Image.open(image1_path).convert("L").resize(target_size)
        image2 = Image.open(image2_path).convert("L").resize(target_size)

        img1_arr = np.array(image1)
        img2_arr = np.array(image2)

        # 確保 win_size 為奇數且不超過圖片尺寸
        min_dim = min(img1_arr.shape[:2])
        win_size = min(7, min_dim)
        if win_size % 2 == 0:  # 如果是偶數，減 1 變奇數
            win_size -= 1

        if win_size < 3:
            print(f"圖片尺寸 ({min_dim}) 太小，無法滿足最小 win_size=3")
            return 0.0

        # 指定 data_range=255 (因為是 uint8 0-255)
        ssim_value = ssim(img1_arr, img2_arr, 
                          win_size=win_size, 
                          data_range=255)
        
        return ssim_value

    except Exception as e:
        print(f"SSIM 計算失敗：{e}")
        return 0.0
    

def compare_handwritings(folder_path, my_handwriting_paths):
    """ 比較手寫字圖片相似度，回傳 DataFrame """
    results = []

    # 過濾出圖片檔案
    images_to_compare = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.lower().endswith(('png', 'jpg', 'jpeg'))
    ]

    for my_handwriting_path in my_handwriting_paths:
        for image_path in images_to_compare:
            lpips_distance = compute_lpips_distance(my_handwriting_path, image_path)
            ssim_value = compute_ssim(my_handwriting_path, image_path)
            results.append((os.path.basename(image_path), lpips_distance, ssim_value))

    # 建立 DataFrame
    df = pd.DataFrame(results, columns=['Student', 'LPIPS', 'SSIM'])
    df.sort_values(by='LPIPS', inplace=True)

    return df

# 設定資料夾
BASE_DIR = Path(__file__).resolve().parent
folder_path = BASE_DIR / "79CB"
my_handwriting_folder = BASE_DIR / "mine"

# 確保 `mine` 資料夾內有圖片
my_handwriting_images = [
    os.path.join(my_handwriting_folder, f) for f in os.listdir(my_handwriting_folder)
    if f.lower().endswith(('png', 'jpg', 'jpeg'))
]

if not my_handwriting_images:
    raise ValueError("錯誤：'mine' 資料夾內沒有圖片！請確認有 PNG、JPG 或 JPEG 檔案。")

# 執行比對
df = compare_handwritings(folder_path, my_handwriting_images)
print(df)

# 確保 `excel` 資料夾存在
output_folder = BASE_DIR / 'excel'
os.makedirs(output_folder, exist_ok=True)

# 存成 CSV
output_csv_path = os.path.join(output_folder, 'results.csv')
df.to_csv(output_csv_path, index=False)
print(f"結果已儲存至 {output_csv_path}")
