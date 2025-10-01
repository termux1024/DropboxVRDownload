import dropbox, time
from urllib.parse import urlparse, parse_qs
import os

# ====== SETTINGS ======
def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()  # Reads token from dropbox_token.txt
LINKS_FILE = "checkfordevelop.txt"  # File containing URLs, one per line
DROPBOX_FOLDER = "/VR"    # Dropbox folder to save files in
# ======================

dbx = dropbox.Dropbox(ACCESS_TOKEN)

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

for URL_TO_SAVE in urls:
    parsed_url = urlparse(URL_TO_SAVE)
    qs = parse_qs(parsed_url.query)
    if 'fn' in qs:
        file_name = qs['fn'][0]
    else:
        file_name = os.path.basename(parsed_url.path)
    dropbox_path = f"{DROPBOX_FOLDER}/{file_name}"
    try:
        job = dbx.files_save_url(dropbox_path, URL_TO_SAVE)
        print(f"Job started… Dropbox is downloading '{file_name}' in the background.")
        time.sleep(5)  # Slight delay to avoid hitting rate limits
    except Exception as e:
        print(f"Failed to start job for '{file_name}': {e}")