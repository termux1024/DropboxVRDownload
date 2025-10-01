import requests
from urllib.parse import urlparse, parse_qs

LINKS_FILE = "missing_links.txt"

def get_file_name(url):
    parsed_url = urlparse(url)
    qs = parse_qs(parsed_url.query)
    if 'fn' in qs:
        return qs['fn'][0]
    return os.path.basename(parsed_url.path)

def get_file_size(url):
    try:
        response = requests.head(url, allow_redirects=True)
        size = int(response.headers.get('content-length', 0))
        return size
    except Exception as e:
        print(f"Could not get size for {url}: {e}")
        return 0

with open(LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

total_size = 0
for url in urls:
    file_name = get_file_name(url)
    size = get_file_size(url)
    size_gb = size / (1024 ** 3)
    print(f"{file_name}: {size} bytes ({size_gb:.4f} GB)")
    total_size += size

total_gb = total_size / (1024 ** 3)
print(f"\nTotal size of all files: {total_size} bytes ({total_gb:.4f} GB)")