import dropbox
from urllib.parse import urlparse, parse_qs
import os

def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()  # Reads token from dropbox_token.txt
LINKS_FILE = "pornlinks.txt"
DROPBOX_FOLDER = "/VR"
OUTPUT_FILE = "missing_links.txt"

def get_content_name(url):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if 'fn' in qs:
        return qs['fn'][0]
    return os.path.basename(parsed_url.path)

dbx = dropbox.Dropbox(ACCESS_TOKEN)

# 1. List all files in Dropbox folder
dropbox_files = []
result = dbx.files_list_folder(DROPBOX_FOLDER)
for entry in result.entries:
    if isinstance(entry, dropbox.files.FileMetadata):
        dropbox_files.append(entry.name)
while result.has_more:
    result = dbx.files_list_folder_continue(result.cursor)
    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            dropbox_files.append(entry.name)

print("Files in Dropbox /VR folder:")
for f in dropbox_files:
    print(f)

# 2. Parse filenames from links
with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]
link_names = [get_content_name(url) for url in urls]

# 3. Find links whose filenames are not in Dropbox
missing_links = [url for url, name in zip(urls, link_names) if name not in dropbox_files]

# 4. Write missing links to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for url in missing_links:
        f.write(url + "\n")

print(f"\nLinks not downloaded (saved to {OUTPUT_FILE}): {len(missing_links)}")