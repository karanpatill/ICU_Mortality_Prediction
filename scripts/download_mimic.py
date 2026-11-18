import os
import sys
import time
import getpass
import argparse
import requests

PHYSIONET_BASE_FILES = "https://physionet.org/files/mimiciv/3.1"
PHYSIONET_ZIP_URL = "https://physionet.org/content/mimiciv/get-zip/3.1/"

# Essential files needed for Mechanical Ventilation ICU Mortality project:
CORE_FILES = [
    # ICU stays and cohort identifiers
    "icu/icustays.csv.gz",
    # Patient demographics (age, gender, DOD)
    "hosp/patients.csv.gz",
    # Hospital admissions & mortality flags
    "hosp/admissions.csv.gz",
    # Ventilation duration & invasive procedures
    "icu/procedureevents.csv.gz",
    # Intermittent lab measurements (Staleness target!)
    "hosp/labevents.csv.gz",
    # Continuous vitals & ventilator settings (FiO2, PEEP, etc.)
    "icu/chartevents.csv.gz",
]

def format_size(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:3.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def download_file(url, out_path, auth, session):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    temp_path = out_path + ".part"
    
    initial_bytes = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    headers = {}
    if initial_bytes > 0:
        headers["Range"] = f"bytes={initial_bytes}-"
        print(f"  [Resuming] {os.path.basename(out_path)} from {format_size(initial_bytes)}...")

    try:
        with session.get(url, auth=auth, headers=headers, stream=True, timeout=30) as r:
            if r.status_code == 401 or r.status_code == 403:
                print(f"\n[ERROR] Authentication failed (Status {r.status_code}).")
                print("Please verify your PhysioNet username & password, and ensure DUA is signed.")
                return False
            
            if r.status_code not in (200, 206):
                print(f"\n[ERROR] Server returned HTTP {r.status_code} for {url}")
                return False

            total_bytes = int(r.headers.get('content-length', 0)) + initial_bytes
            mode = 'ab' if initial_bytes > 0 else 'wb'
            
            print(f"  Downloading {os.path.basename(out_path)} ({format_size(total_bytes) if total_bytes > initial_bytes else 'unknown size'})...")
            
            downloaded = initial_bytes
            start_time = time.time()
            last_print = start_time
            
            with open(temp_path, mode) as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_print > 1.0 or downloaded >= total_bytes:
                            elapsed = max(now - start_time, 0.001)
                            speed = (downloaded - initial_bytes) / elapsed
                            pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                            print(f"\r    -> {format_size(downloaded)} / {format_size(total_bytes)} [{pct:.1f}%] - {format_size(speed)}/s", end="", flush=True)
                            last_print = now
            print()
            
        # Rename .part to final
        if os.path.exists(out_path):
            os.remove(out_path)
        os.rename(temp_path, out_path)
        print(f"  [COMPLETED] Saved to {out_path}\n")
        return True

    except Exception as e:
        print(f"\n[EXCEPTION] Error downloading {url}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MIMIC-IV v3.1 Resumable Downloader for D: drive")
    parser.add_argument("--username", default="karanpatil", help="PhysioNet username")
    parser.add_argument("--password", default=os.getenv("PHYSIONET_PASSWORD", None), help="PhysioNet password")
    parser.add_argument("--output_dir", default=r"D:\ICU_Mortality_Prediction\data\mimiciv", help="Target output folder")
    parser.add_argument("--mode", choices=["core", "zip"], default="core", 
                        help="'core' downloads only the 6 required tables (~4GB), 'zip' downloads full 9.8GB archive")
    args = parser.parse_args()

    print("=" * 70)
    print(" MIMIC-IV v3.1 Resumable Direct Downloader (Target: D: Drive)")
    print("=" * 70)
    print(f" Destination Directory: {args.output_dir}")
    print(f" PhysioNet Username   : {args.username}")
    print(f" Download Mode        : {args.mode.upper()}")
    print("=" * 70)

    username = args.username
    password = args.password

    if not password:
        password = getpass.getpass(f"Enter PhysioNet password for user '{username}': ")

    auth = (username, password)
    session = requests.Session()

    # Quick verify authentication using icustays head request
    test_url = f"{PHYSIONET_BASE_FILES}/icu/icustays.csv.gz"
    print("\nVerifying PhysioNet credentials...")
    try:
        r = session.head(test_url, auth=auth, timeout=15)
        if r.status_code in (200, 302):
            print(">>> Credentials verified successfully! Access granted.\n")
        elif r.status_code in (401, 403):
            print(f">>> [FAIL] Authentication failed (HTTP {r.status_code}).")
            print("Please check your password or ensure you have accepted the MIMIC-IV Data Use Agreement on PhysioNet.")
            sys.exit(1)
        else:
            print(f">>> Warning: Verification returned status {r.status_code}. Proceeding anyway...")
    except Exception as e:
        print(f">>> Connection error during auth check: {e}")
        sys.exit(1)

    if args.mode == "zip":
        zip_out = os.path.join(args.output_dir, "mimic-iv-3.1.zip")
        success = download_file(PHYSIONET_ZIP_URL, zip_out, auth, session)
        if success:
            print(f"\nAll done! MIMIC-IV zip saved to {zip_out}")
    else:
        print(f"Downloading {len(CORE_FILES)} core project tables into {args.output_dir}...")
        for rel_file in CORE_FILES:
            file_url = f"{PHYSIONET_BASE_FILES}/{rel_file}"
            file_out = os.path.join(args.output_dir, rel_file.replace("/", os.sep))
            
            if os.path.exists(file_out):
                print(f"  [Already Exists] Skipping {rel_file} ({format_size(os.path.getsize(file_out))})")
                continue
                
            success = download_file(file_url, file_out, auth, session)
            if not success:
                print(f"[WARNING] Failed to download {rel_file}. You can re-run this script to resume.")
                sys.exit(1)

        print("\n" + "=" * 70)
        print(" SUCCESS! All core MIMIC-IV tables downloaded to D: drive.")
        print(" Ready to filter mechanical ventilation cohort and run models!")
        print("=" * 70)

if __name__ == "__main__":
    main()
