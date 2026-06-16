"""
run_all.py - Menjalankan semua script secara berurutan
"""

import subprocess
import sys
import os
from datetime import datetime

def run_script(script_path):
    print(f"\n{'='*60}")
    print(f"[RUN] Menjalankan: {script_path}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[WARNING] Errors:", result.stderr)
    return result.returncode == 0

def main():
    start_time = datetime.now()
    print("[START] Memulai pipeline analisis...")
    print(f"[TIME] Waktu: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    scripts = [
        'scripts/fetch_macro_data.py',
        'scripts/filter_news.py',
        'scripts/generate_signals.py'
    ]
    
    success = True
    for script in scripts:
        if not run_script(script):
            success = False
            print(f"[FAIL] Gagal pada: {script}")
            break
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    if success:
        print("[OK] SEMUA PROSES SELESAI!")
    else:
        print("[FAIL] PROSES GAGAL!")
    print(f"[TIME] Durasi: {duration:.2f} detik")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()