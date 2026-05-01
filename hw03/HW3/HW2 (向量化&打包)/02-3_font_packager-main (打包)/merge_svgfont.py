import re
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    def tqdm(iterable, **kwargs):
        return iterable


FONT_NAME = "MyFont"
CANVAS_SIZE = 300
TARGET_GLYPH_SIZE = 240
MAX_GLYPH_SCALE = 2.20
GLYPH_PADDING = 8
SPACE_WIDTH = 90
LATIN_GLYPH_SCALE = 1.75
LATIN_BASELINE_Y = 35
LATIN_DESCENDER_BASELINE_Y = -10
SOURCE_FONT = "notosanschar"

FONT_SOURCE_ORDER = {
    "MOE4808": ["MOE4808"],
    "big5": ["big5", "MOE4808"],
    "notosanschar": ["notosanschar", "big5", "MOE4808"],
}


def transform_point(x, y, scale):
    center = CANVAS_SIZE / 2
    scaled_x = center + (x - center) * scale
    flipped_y = CANVAS_SIZE - y
    scaled_y = center + (flipped_y - center) * scale
    return scaled_x, scaled_y


def is_latin_glyph(hex_code):
    codepoint = int(hex_code, 16)
    return 0x0021 <= codepoint <= 0x007E


def is_latin_descender(hex_code):
    return int(hex_code, 16) in {ord(char) for char in "gjpqy"}


def transform_path(raw_d, hex_code):
    tokens = re.findall(r"([a-zA-Z])|([-+]?\d*\.\d+|[-+]?\d+)", raw_d)
    entries = []
    pending_x = None
    raw_points = []

    for cmd, val in tokens:
        if cmd:
            pending_x = None
            continue

        num = float(val)
        if pending_x is None:
            pending_x = num
        else:
            raw_points.append((pending_x, CANVAS_SIZE - num))
            pending_x = None

    if is_latin_glyph(hex_code):
        scale = LATIN_GLYPH_SCALE
    elif raw_points:
        xs = [x for x, _ in raw_points]
        ys = [y for _, y in raw_points]
        max_dim = max(max(xs) - min(xs), max(ys) - min(ys))
        scale = min(MAX_GLYPH_SCALE, TARGET_GLYPH_SIZE / max_dim) if max_dim else 1
    else:
        scale = 1

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
            x, y = transform_point(pending_x, num, scale)
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

    if is_latin_glyph(hex_code) and ys:
        min_y = min(ys)
        baseline_y = LATIN_DESCENDER_BASELINE_Y if is_latin_descender(hex_code) else LATIN_BASELINE_Y
        dy = baseline_y - min_y
    elif ys:
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


def get_input_folders(hw3_dir):
    workspace_dir = hw3_dir.parent.parent
    handwritten_folder = workspace_dir / "hw02" / "HW2" / "02-3_font_packager-main" / "pico"
    svg_pico_dir = hw3_dir / "generated_font" / "svg_pico"

    source_names = FONT_SOURCE_ORDER.get(SOURCE_FONT)
    if source_names is None:
        raise ValueError(f"Unknown SOURCE_FONT: {SOURCE_FONT}")

    folders = [svg_pico_dir / source_name for source_name in source_names]
    folders.append(handwritten_folder)
    return folders


def collect_svg_files(input_folders):
    svg_by_hex = {}

    for input_folder in input_folders:
        if not input_folder.exists():
            print(f"Skip missing folder: {input_folder}")
            continue

        svg_files = sorted(input_folder.glob("*.svg"))
        print(f"Add source: {input_folder} ({len(svg_files)} svg)")

        for svg_path in svg_files:
            match = re.search(r"[Uu]\+([0-9A-Fa-f]+)", svg_path.name)
            if not match:
                continue

            hex_code = match.group(1).upper()
            svg_by_hex[hex_code] = svg_path

    return sorted(svg_by_hex.items(), key=lambda item: int(item[0], 16))


def create_svg_font_with_flip():
    script_dir = Path(__file__).resolve().parent
    hw3_dir = script_dir.parent.parent

    input_folders = get_input_folders(hw3_dir)
    output_dir = hw3_dir / "generated_font" / "final_font" / SOURCE_FONT
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
    <glyph glyph-name="space" unicode="&#x20;" horiz-adv-x="{SPACE_WIDTH}" />
    <glyph glyph-name="nbsp" unicode="&#xA0;" horiz-adv-x="{SPACE_WIDTH}" />
    <glyph glyph-name="ideographic_space" unicode="&#x3000;" horiz-adv-x="{CANVAS_SIZE}" />
'''

    glyph_definitions = []
    svg_files = collect_svg_files(input_folders)

    for hex_code, svg_path in tqdm(svg_files, desc="Merge SVG"):
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

            transformed_d = transform_path(raw_d, hex_code)
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
