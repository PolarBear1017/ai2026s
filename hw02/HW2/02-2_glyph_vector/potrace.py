import os
import subprocess
import time
from pathlib import Path
from tqdm import tqdm
from PIL import Image, ImageFilter


input_dir = Path("./png")
output_dir = Path("./output")
output_dir.mkdir(parents=True, exist_ok=True)

png_files = list(input_dir.glob("*.png"))

if not png_files:
    print("Cannot find .png")
else:
    start_time = time.time()
    
    for img_path in tqdm(png_files, desc="Conversion Progress"):
        svg_path = output_dir / f"{img_path.stem}.svg"
        temp_bmp = img_path.with_suffix(".bmp")

        try:
            with Image.open(img_path) as img:
                img = img.convert("L")
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5)) 
                # GaussianBlur 調整半徑使筆畫圓滑，要保留書法感 = 0.5
                
                # threshold 灰階閥值
                # 調高 threshold 筆畫收縮
                threshold = 140 
                binary_img = img.point(lambda p: 255 if p > threshold else 0, mode='1')
                binary_img.save(temp_bmp)

            # Potrace 核心參數
            # --turdsize x: 忽略 x 像素的雜點
            # --alphamax x: 曲線平滑度
            # --opttolerance 0.2: 曲線優化容差
            subprocess.run(
                [
                    "potrace.exe", 
                    "-s", 
                    "--turdsize", "20", 
                    "--alphamax", "0.8",  # 保留書法感
                    "--opttolerance", "0.2",
                    str(temp_bmp), 
                    "-o", str(svg_path)
                ],
                check=True,
                capture_output=True
            )
            
            if temp_bmp.exists():
                os.remove(temp_bmp)

        except Exception as e:
            print(f"convert {img_path.name} failed: {e}")

    end_time = time.time()
    print(f"Conversion complete :) Time taken: {end_time - start_time:.2f} seconds")