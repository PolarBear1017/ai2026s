import re
import xml.etree.ElementTree as ET
from pathlib import Path

from tqdm import tqdm


FONT_NAME = "MyFont"
CANVAS_SIZE = 300
GLYPH_SCALE = 1.40
GLYPH_PADDING = 6


def transform_point(x, y):
    center = CANVAS_SIZE / 2
    scaled_x = center + (x - center) * GLYPH_SCALE
    flipped_y = CANVAS_SIZE - y
    scaled_y = center + (flipped_y - center) * GLYPH_SCALE
    return scaled_x, scaled_y


def transform_path(raw_d):
    tokens = re.findall(r"([a-zA-Z])|([-+]?\d*\.\d+|[-+]?\d+)", raw_d)
    entries = []
    pending_x = None

    for cmd, val in tokens:
        if cmd:
            entries.append(("cmd", cmd))
            pending_x = None
            continue

        num = float(val)
        if pending_x is None:
            pending_x = num
        else:
            x, y = transform_point(pending_x, num)
            entries.append(("x", x))
            entries.append(("y", y))
            pending_x = None

    if pending_x is not None:
        entries.append(("num", pending_x))

    xs = [value for axis, value in entries if axis == "x"]
    ys = [value for axis, value in entries if axis == "y"]
    dx = dy = 0

    if xs:
        min_x, max_x = min(xs), max(xs)
        if min_x < GLYPH_PADDING:
            dx = GLYPH_PADDING - min_x
        elif max_x > CANVAS_SIZE - GLYPH_PADDING:
            dx = CANVAS_SIZE - GLYPH_PADDING - max_x

    if ys:
        min_y, max_y = min(ys), max(ys)
        if min_y < GLYPH_PADDING:
            dy = GLYPH_PADDING - min_y
        elif max_y > CANVAS_SIZE - GLYPH_PADDING:
            dy = CANVAS_SIZE - GLYPH_PADDING - max_y

    new_tokens = []
    for axis, value in entries:
        if axis == "cmd":
            new_tokens.append(value)
        elif axis == "x":
            new_tokens.append(format(value + dx, ".2f"))
        elif axis == "y":
            new_tokens.append(format(value + dy, ".2f"))
        else:
            new_tokens.append(format(value, ".2f"))

    return " ".join(new_tokens)


def create_svg_font_with_flip():
    input_folder = Path("pico")
    output_dir = Path("final_font")
    output_path = output_dir / "fontpico.svg"

    output_dir.mkdir(parents=True, exist_ok=True)

    svg_header = f'''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" >
<svg xmlns="http://www.w3.org/2000/svg">
<defs>
  <font id="{FONT_NAME}" horiz-adv-x="{CANVAS_SIZE}">
    <font-face font-family="{FONT_NAME}"
      units-per-em="{CANVAS_SIZE}" ascent="{CANVAS_SIZE}"
      descent="0" />
    <missing-glyph horiz-adv-x="0" />
'''

    glyph_definitions = []
    svg_files = sorted(input_folder.glob("*.svg"))

    for svg_path in tqdm(svg_files, desc="Merge SVG"):
        match = re.search(r"[Uu]\+([0-9A-Fa-f]+)", svg_path.name)
        if not match:
            continue

        hex_code = match.group(1).upper()
        glyph_name = f"icon_{hex_code}"
        unicode_entity = f"&#x{hex_code};"

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            ns = {"svg": "http://www.w3.org/2000/svg"}
            paths = root.findall(".//svg:path", ns) or root.findall(".//path")
            raw_d = " ".join(p.attrib.get("d", "") for p in paths)

            if not raw_d:
                continue

            transformed_d = transform_path(raw_d)
            glyph_definitions.append(
                f'    <glyph glyph-name="{glyph_name}"\n'
                f'      unicode="{unicode_entity}"\n'
                f'      horiz-adv-x="{CANVAS_SIZE}" d="{transformed_d}" />'
            )

        except Exception as e:
            print(f"Failed to process {svg_path.name}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_header)
        f.write("\n".join(glyph_definitions))
        f.write("\n  </font>\n</defs>\n</svg>")

    print(f"SVG Font: {output_path}")


if __name__ == "__main__":
    create_svg_font_with_flip()
