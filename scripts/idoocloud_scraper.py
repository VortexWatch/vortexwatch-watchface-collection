import requests
import os
import time
import csv
from datetime import datetime

# API Config
API_URL = "https://in-device.idoocloud.com/api/device/face/v4/get"
HEADERS = {
    "appkey": "548a50bc9f0a45d0bdfcdb5d194641d8",
    "X-HB-Client-Type": "ayb-android",
    "User-Agent": "okhttp/4.12.0"
}

# Directories
BASE_DIR = "Scraped_Watchfaces"
LOG_FILE = "full_scrape_log.txt"
MANIFEST_FILE = "master_manifest.csv"

# Hardware Profile
BASE_PARAMS = {
    "language": "en",
    "appFaceVersion": "1",
    "supportFaceVersion": "3",
    "otaVersion": "15",
    "withoutVipFlag": "false",
    "os.type": "2",
    "os.version": "16",
    "d.name": "7264",
    "d.version": "15",
    "m.name": "M2101K7AI",
    "app.version": "3.2.1",
    "nid": "3128df22526d8185",
    "locale": "en_in",
    "country": "IN"
}

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def init_manifest():
    if not os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Resolution", "MD5", "Size_Bytes", "Download_URL"])

async def nuclear_scrape(start_id, end_id):
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    
    init_manifest()
    log(f"--- STARTING NUCLEAR SCRAPE: {start_id} TO {end_id} ---")

    for face_id in range(start_id, end_id + 1):
        params = BASE_PARAMS.copy()
        params["id"] = face_id

        try:
            response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result")

                if result and data.get("status") == 200:
                    name = result.get("otaFaceName", "unknown")
                    ota = result.get("otaFaceVersion", {})
                    url = ota.get("linkUrl")
                    md5 = ota.get("md5", "N/A")
                    size = ota.get("size", 0)
                    res = result.get("resolution", "Unknown")

                    if url:
                        print(f"[+] ID {face_id}: Found {name} ({res})")
                        download_file(url, name, face_id)
                        
                        # Add to Manifest
                        with open(MANIFEST_FILE, "a", newline='', encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow([face_id, name, res, md5, size, url])
                        
                        log(f"SUCCESS: ID {face_id} | {name} | {url}")
                    else:
                        print(f"[-] ID {face_id}: Metadata exists but URL is missing.")
                        log(f"MISSING_URL: ID {face_id}")
                else:
                    print(f"[-] ID {face_id}: Empty (Does not exist)")
                    log(f"EMPTY: ID {face_id}")
            else:
                print(f"[!] ID {face_id}: HTTP {response.status_code}")
                log(f"HTTP_ERROR: ID {face_id} | {response.status_code}")

        except Exception as e:
            print(f"[!] ID {face_id}: Exception {str(e)}")
            log(f"EXCEPTION: ID {face_id} | {str(e)}")

        # Respect the server to avoid IP bans
        time.sleep(0.15)

def download_file(url, name, face_id):
    # Sanitize name for Windows file system
    clean_name = "".join([c for c in name if c.isalnum() or c in (' ', '.', '_')]).strip()
    filename = f"ID{face_id}_{clean_name}.zip"
    filepath = os.path.join(BASE_DIR, filename)

    if os.path.exists(filepath):
        print(f"    -> Already in library.")
        return

    try:
        r = requests.get(url, stream=True, timeout=20)
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=16384):
                f.write(chunk)
        print(f"    -> Downloaded successfully.")
    except:
        print(f"    [!] Download failed for {name}")

if __name__ == "__main__":
    import asyncio
    # Executing range 6000 to 49000
    try:
        asyncio.run(nuclear_scrape(6000, 49000))
    except KeyboardInterrupt:
        print("\n[!] Scrape paused by user.")
