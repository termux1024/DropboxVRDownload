import dropbox
import requests
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

# ====== SETTINGS ======
def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()
LINKS_FILE = "checkfordevelop.txt"
DROPBOX_FOLDER = "/VR"
TEMP_DIR = "temp_downloads"
os.makedirs(TEMP_DIR, exist_ok=True)
# ======================

dbx = dropbox.Dropbox(ACCESS_TOKEN)

def get_file_name(url):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if 'fn' in qs:
        return qs['fn'][0]
    return os.path.basename(parsed_url.path)

def download_file(url):
    file_name = get_file_name(url)
    local_path = os.path.join(TEMP_DIR, file_name)
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded: {file_name}")
        return local_path, file_name
    except Exception as e:
        print(f"Download failed for {file_name}: {e}")
        return None, file_name

def upload_file(local_path, file_name):
    dropbox_path = f"{DROPBOX_FOLDER}/{file_name}"
    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"Uploaded: {file_name}")
        os.remove(local_path)
    except Exception as e:
        print(f"Upload failed for {file_name}: {e}")

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# Download up to 4 files at a time
with ThreadPoolExecutor(max_workers=4) as download_executor, ThreadPoolExecutor(max_workers=2) as upload_executor:
    future_to_url = {download_executor.submit(download_file, url): url for url in urls}
    upload_futures = []
    for future in as_completed(future_to_url):
        local_path, file_name = future.result()
        if local_path:
            # Start upload (up to 2 at a time)
            upload_futures.append(upload_executor.submit(upload_file, local_path, file_name))
    # Wait for all uploads to finish
    for uf in as_completed(upload_futures):
        uf.result()