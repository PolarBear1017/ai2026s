# 感謝資工四張睿恩提供此程式

import os
import sys
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

def get_venv_script(command_name):
    exe_name = f"{command_name}.exe" if os.name == "nt" else command_name
    candidate = Path(sys.executable).parent / exe_name
    return str(candidate) if candidate.exists() else command_name

def get_inkscape_command():
    common_paths = [
        Path(r"C:\Program Files\Inkscape\bin\inkscape.exe"),
        Path(r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe"),
    ]
    for path in common_paths:
        if path.exists():
            return str(path)
    return "inkscape"

def convert_with_timeout(svg_file, png_dir, output_size=300, timeout_seconds=60):
    """
    Convert SVG to PNG with timeout.
    First try cairosvg, if timeout then fallback to inkscape.
    Returns (success: bool, filename: str, message: str)
    """
    png_path = Path(png_dir) / f"{Path(svg_file).stem}.png"
    
    # Try cairosvg first
    try:
        result = subprocess.run(
            [get_venv_script("cairosvg"), str(svg_file), "-o", str(png_path), "-W", str(output_size), "-H", str(output_size), "-b", "white"],
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode == 0:
            return (True, Path(svg_file).name, "Success (cairosvg)")
        else:
            # If cairosvg fails, try inkscape
            return _try_inkscape(svg_file, png_path, output_size, timeout_seconds, result.stderr)
            
    except subprocess.TimeoutExpired:
        # cairosvg timed out, try inkscape as fallback
        return _try_inkscape(svg_file, png_path, output_size, timeout_seconds, "cairosvg timed out")
    except Exception as e:
        # cairosvg not found or other error, try inkscape
        return _try_inkscape(svg_file, png_path, output_size, timeout_seconds, str(e))

def _try_inkscape(svg_file, png_path, output_size, timeout_seconds, cairosvg_error=""):
    """加上環境變數與重試機制，徹底解決 D-Bus 錯誤並確保白底"""
    import os
    import time
    
    # 禁用 D-Bus，因為會報錯 (error code: DBus::Error)
    custom_env = os.environ.copy()
    custom_env["DBUS_SESSION_BUS_ADDRESS"] = "" 
    
    max_retries = 3  # 最多重試 3 次
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    get_inkscape_command(), 
                    str(svg_file), 
                    "--export-type=png", 
                    f"--export-filename={png_path}", 
                    f"--export-width={output_size}", 
                    f"--export-height={output_size}",
                    "--export-background=white",
                    "--export-background-opacity=255"
                ],
                timeout=timeout_seconds,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=custom_env
            )
            
            if result.returncode == 0:
                return (True, Path(svg_file).name, "Success (inkscape)")
            
            # 如果有錯誤可以重試
            if "DBus" in result.stderr or "Gio" in result.stderr:
                time.sleep(1)
                continue
                
            return (False, Path(svg_file).name, f"Error: {result.stderr[:100]}")
            
        except subprocess.TimeoutExpired:
            if attempt == max_retries - 1:
                return (False, Path(svg_file).name, f"Timeout after {timeout_seconds}s")
            time.sleep(1)
        except Exception as e:
            details = f"cairosvg failed: {cairosvg_error[:300]} | inkscape failed: {str(e)}"
            return (False, Path(svg_file).name, details)
            
    return (False, Path(svg_file).name, "Failed after multiple retries due to DBus/System error")

def main():
    # Paths
    svg_dir = Path(__file__).parent / "svg"
    png_dir = Path(__file__).parent / "png"
    
    # Create output directory
    png_dir.mkdir(exist_ok=True)
    
    # Get all SVG files
    svg_files = sorted(list(svg_dir.glob("U+*.svg")))
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}")
        return
    
    print(f"Found {len(svg_files)} SVG files")
    print(f"Converting to PNG (timeout: 60s per file, 4 parallel workers)\n")
    
    # Counter for results
    success_count = 0
    timeout_count = 0
    error_count = 0
    
    # Parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all conversion tasks
        futures = {
            executor.submit(convert_with_timeout, svg_file, png_dir, timeout_seconds=60): svg_file
            for svg_file in svg_files
        }
        
        # Process results as they complete
        with tqdm(total=len(svg_files), desc="Converting SVG to PNG") as pbar:
            for future in as_completed(futures):
                success, filename, message = future.result()
                
                if success:
                    success_count += 1
                elif "Timeout" in message:
                    timeout_count += 1
                    print(f"\n{filename}: {message}")
                else:
                    error_count += 1
                    print(f"\n{filename}: {message}")
                
                pbar.update(1)
    
    # Print summary
    print(f"\n\nConversion Summary:")
    print(f"  Successful: {success_count}/{len(svg_files)}")
    print(f"  Timeout:   {timeout_count}/{len(svg_files)}")
    print(f"  Failed:    {error_count}/{len(svg_files)}")
    
    png_files = list(png_dir.glob("*.png"))
    print(f"  Generated {len(png_files)} PNG files")


if __name__ == "__main__":
    main()
