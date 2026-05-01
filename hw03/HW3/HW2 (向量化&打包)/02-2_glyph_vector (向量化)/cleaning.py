import shutil
from pathlib import Path
from collections import defaultdict

def collect_glyphs_for_review(base_dir="crop", review_dir="to_be_reviewed", ext=".png"):
    base_path = Path(base_dir)
    rev_path = Path(review_dir)
    rev_path.mkdir(parents=True, exist_ok=True)

    # defaultdict: 當存取不存在的key，會自動建立預設值
    # 記錄所有crop底下的字的來源路徑的字典，value: data type --> list
    glyph_map = defaultdict(list)
    
    # 掃描開頭為 crop_ 的資料夾
    subfolders = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("crop_")]
    
    # rglob (Recursive Glob): 翻遍這個資料夾以及它下面所有的子資料夾
    for folder in subfolders:
        for file_path in folder.rglob(f"*{ext}"):
            # 去除編號後綴
            glyph_name = file_path.stem.split('-')[0].split('_')[0]
            glyph_map[glyph_name].append(file_path)


    for glyph, files in glyph_map.items():
        # 有重複字
        glyph_font = str(chr(int(glyph[2:6], 16)))
        if len(files) > 1:
            target_folder = rev_path / glyph_font
            target_folder.mkdir(exist_ok=True)
            for f in files:
                new_name = f"{f.parent.name}_{f.name}"
                shutil.copy2(f, target_folder / new_name)
        
        # 只有一個的字
        else:
            unique_folder = rev_path / "_unique_items"
            unique_folder.mkdir(exist_ok=True)
            shutil.copy2(files[0], unique_folder / files[0].name)

    print(f"======= 分類完成 ========")
    print(f"重複字已放入 {review_dir}")
    print("非重複字在 _unique_items")
# 執行
collect_glyphs_for_review()