import shutil
from pathlib import Path

def merge_final_dataset(review_dir="to_be_reviewed", output_dir="final_dataset"):
    rev_path = Path(review_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 處理 to_be_reviewed
    for glyph_folder in rev_path.iterdir():
        if glyph_folder.is_dir() and not glyph_folder.name.startswith("_"):
            
            candidates = list(glyph_folder.glob("*.png"))
            
            if candidates:
                # 避免有沒選擇完的字，直接優先挑選檔案容量最大的
                selected_one = max(candidates, key=lambda x: x.stat().st_size)
                glyph_unicode = hex(ord(glyph_folder.name))[2:6]
                target_name = f"U+{glyph_unicode}.png"
                shutil.copy2(selected_one, out_path / target_name)
                
                # 告知使用者這些字沒刪乾淨
                if len(candidates) > 1:
                    print(f"{glyph_folder.name}: 尚存 {len(candidates)} 個檔案，已自動挑選：{selected_one.name}")

    # 處理 _unique_items
    unique_path = rev_path / "_unique_items"
    if unique_path.exists():
        for f in unique_path.glob("*.png"):
            # 檔名清洗，只留下 U+****
            clean_name = f.stem.split('-')[0].split('_')[0]
            shutil.copy2(f, out_path / f"{clean_name}.png")

    print(f"\n======= 合併完成 ========")
    print(f"輸出到 {output_dir}")

# 執行合併
merge_final_dataset()