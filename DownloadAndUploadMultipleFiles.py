import dropbox
import requests
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import shutil

# ====== SETTINGS ======
def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()
LINKS_FILE = "missing_links.txt"  # File containing URLs, one per line
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
            with open(local_path, 'wb') as f, tqdm(
                desc=f"Downloading {file_name}",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        return local_path, file_name
    except Exception as e:
        print(f"Download failed for {file_name}: {e}")
        return None, file_name

def upload_file(local_path, file_name):
    dropbox_path = f"{DROPBOX_FOLDER}/{file_name}"
    try:
        file_size = os.path.getsize(local_path)
        CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
        with open(local_path, "rb") as f, tqdm(
            desc=f"Uploading {file_name}",
            total=file_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            if file_size <= 150 * 1024 * 1024:
                data = f.read()
                dbx.files_upload(data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                bar.update(file_size)
            else:
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                bar.update(CHUNK_SIZE)
                cursor = dropbox.files.UploadSessionCursor(
                    session_id=upload_session_start_result.session_id,
                    offset=f.tell()
                )
                commit = dropbox.files.CommitInfo(path=dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                while f.tell() < file_size:
                    if (file_size - f.tell()) <= CHUNK_SIZE:
                        chunk = f.read(CHUNK_SIZE)
                        dbx.files_upload_session_finish(chunk, cursor, commit)
                        bar.update(len(chunk))
                    else:
                        chunk = f.read(CHUNK_SIZE)
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = f.tell()
                        bar.update(len(chunk))
        os.remove(local_path)
    except Exception as e:
        print(f"Upload failed for {file_name}: {e}")

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as download_executor, ThreadPoolExecutor(max_workers=2) as upload_executor:
        future_to_url = {download_executor.submit(download_file, url): url for url in urls}
        upload_futures = []
        for future in as_completed(future_to_url):
            local_path, file_name = future.result()
            if local_path:
                upload_futures.append(upload_executor.submit(upload_file, local_path, file_name))
        for uf in as_completed(upload_futures):
            uf.result()

    # Run CombinedDropboxRunner.py after all uploads are done
    import runpy
    runpy.run_path("CombinedDropboxRunner.py")