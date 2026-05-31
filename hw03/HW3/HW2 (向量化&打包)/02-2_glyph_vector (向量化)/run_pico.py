import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

script_dir = Path(__file__).resolve().parent
hw3_dir = script_dir.parent.parent

font_name = "notosanschar"
input_folder = hw3_dir / "generated_font" / "svg" / font_name
output_folder = hw3_dir / "generated_font" / "svg_pico" / font_name

concurrency = 20

def get_venv_script(command_name):
    exe_name = f"{command_name}.exe" if os.name == "nt" else command_name
    candidate = Path(sys.executable).parent / exe_name
    return str(candidate) if candidate.exists() else command_name

def process_single_file(filename):
    if not filename.endswith(".svg"): return
    
    output_folder.mkdir(parents=True, exist_ok=True)
    input_path = input_folder / filename
    output_path = output_folder / filename
    
    try:
        with open(output_path, "w") as out_file:
            subprocess.run([get_venv_script("picosvg"), str(input_path)], stdout=out_file, check=True)
        print(f"Successfully processed: {filename}")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    output_folder.mkdir(parents=True, exist_ok=True)
        
    start_time = time.time()
    files = os.listdir(input_folder)

    # 使用 ThreadPoolExecutor 並行處理
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        executor.map(process_single_file, files)

    end_time = time.time()
    print(f"Conversion complete! Time taken: {end_time - start_time:.2f} seconds")
