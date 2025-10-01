import dropbox
import requests
import os
from urllib.parse import urlparse, parse_qs
import shutil
import time

# ====== SETTINGS ======
def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()
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

def has_enough_space(required_bytes, path=TEMP_DIR):
    total, used, free = shutil.disk_usage(path)
    return free > required_bytes

def download_file(url):
    file_name = get_file_name(url)
    local_path = os.path.join(TEMP_DIR, file_name)
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            if not has_enough_space(total_size):
                print(f"Skipping {file_name}: Not enough disk space ({total_size} bytes needed).")
                return None, file_name
            downloaded = 0
            last_report = time.time()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_report >= 3 or downloaded == total_size:
                            percent = (downloaded / total_size) * 100 if total_size else 0
                            print(f"Downloading {file_name}: {percent:.2f}%")
                            last_report = now
        return local_path, file_name
    except Exception as e:
        print(f"Download failed for {file_name}: {e}")
        return None, file_name

def upload_file(local_path, file_name):
    dropbox_path = f"{DROPBOX_FOLDER}/{file_name}"
    try:
        file_size = os.path.getsize(local_path)
        CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
        uploaded = 0
        last_report = time.time()
        with open(local_path, "rb") as f:
            if file_size <= 150 * 1024 * 1024:
                data = f.read()
                dbx.files_upload(data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                uploaded = file_size
                print(f"Uploading {file_name}: 100.00%")
            else:
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                uploaded += CHUNK_SIZE
                cursor = dropbox.files.UploadSessionCursor(
                    session_id=upload_session_start_result.session_id,
                    offset=f.tell()
                )
                commit = dropbox.files.CommitInfo(path=dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                while f.tell() < file_size:
                    if (file_size - f.tell()) <= CHUNK_SIZE:
                        chunk = f.read(CHUNK_SIZE)
                        dbx.files_upload_session_finish(chunk, cursor, commit)
                        uploaded = file_size
                        print(f"Uploading {file_name}: 100.00%")
                    else:
                        chunk = f.read(CHUNK_SIZE)
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = f.tell()
                        uploaded += len(chunk)
                        now = time.time()
                        if now - last_report >= 3:
                            percent = (uploaded / file_size) * 100 if file_size else 0
                            print(f"Uploading {file_name}: {percent:.2f}%")
                            last_report = now
        os.remove(local_path)
    except Exception as e:
        print(f"Upload failed for {file_name}: {e}")

if __name__ == "__main__":
    url = input("Enter the link to download and upload: ").strip()
    local_path, file_name = download_file(url)
    if local_path:
        upload_file(local_path, file_name)