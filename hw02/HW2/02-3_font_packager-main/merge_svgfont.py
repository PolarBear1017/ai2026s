import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from tqdm import tqdm

def create_svg_font_with_flip():
    font_name = 'MyFont'
    input_folder = Path('pico')
    output_dir = Path('final_font')
    output_path = output_dir / 'fontpico.svg'
    
    output_dir.mkdir(parents=True, exist_ok=True)

    svg_header = f'''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" >
<svg xmlns="http://www.w3.org/2000/svg">
<defs>
  <font id="{font_name}" horiz-adv-x="300">
    <font-face font-family="{font_name}"
      units-per-em="300" ascent="300"
      descent="0" />
    <missing-glyph horiz-adv-x="0" />
'''
    
    glyph_definitions = []
    svg_files = sorted(list(input_folder.glob("*.svg")))

    # 翻轉參數：畫布高度為 300
    canvas_height = 300

    for svg_path in tqdm(svg_files, desc="Merge SVG: "):
        match = re.search(r'[Uu]\+([0-9A-Fa-f]+)', svg_path.name)
        if not match:
            continue
        
        hex_code = match.group(1).upper()
        glyph_name = f"icon_{hex_code}"
        unicode_entity = f"&#x{hex_code};"
        
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            paths = root.findall('.//svg:path', ns) or root.findall('.//path')
            raw_d = " ".join([p.attrib.get('d', '') for p in paths])
            
            if not raw_d:
                continue

            # 正則表達式抓取指令(字母)與數字
            tokens = re.findall(r"([a-zA-Z])|([-+]?\d*\.\d+|\d+)", raw_d)
            
            new_tokens = []
            is_x = True # 座標 (X, Y)
            
            for cmd, val in tokens:
                if cmd: # 如果是指令 (M, L, C, Z...)
                    new_tokens.append(cmd)
                    # 書法字常見指令通常接 X, Y
                    is_x = True 
                elif val: # 如果是數字
                    num = float(val)
                    if is_x:
                        # X 座標保持不變
                        new_tokens.append(format(num, '.2f'))
                        is_x = False
                    else:
                        # Y 座標翻轉：新 Y = 畫布高度 - 舊 Y
                        # 這樣原本在頂部(0)的會變到底部(300)，達成垂直翻轉
                        flipped_y = canvas_height - num
                        new_tokens.append(format(flipped_y, '.2f'))
                        is_x = True

            flipped_d = " ".join(new_tokens)

            # 產出 glyph 標籤
            glyph_def = f'    <glyph glyph-name="{glyph_name}"\n' \
                        f'      unicode="{unicode_entity}"\n' \
                        f'      horiz-adv-x="300" d="{flipped_d}" />'
            glyph_definitions.append(glyph_def)
            
        except Exception as e:
            print(f"Failed to process {svg_path.name}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_header)
        f.write("\n".join(glyph_definitions))
        f.write('\n  </font>\n</defs>\n</svg>')

    print(f"SVG Font：{output_path}")

if __name__ == "__main__":
    create_svg_font_with_flip()