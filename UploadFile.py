import dropbox
import os

# ====== SETTINGS ======
def read_access_token(token_file="dropbox_token.txt"):
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

ACCESS_TOKEN = read_access_token()
DROPBOX_FOLDER = "/VR"
TEMP_DIR = "temp_downloads"
# ======================

dbx = dropbox.Dropbox(ACCESS_TOKEN)

def upload_file(local_path, file_name):
    dropbox_path = f"{DROPBOX_FOLDER}/{file_name}"
    try:
        file_size = os.path.getsize(local_path)
        CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
        uploaded = 0
        if file_size <= 150 * 1024 * 1024:
            with open(local_path, "rb") as f:
                data = f.read()
                dbx.files_upload(data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            print(f"Uploaded {file_name}: 100.00%")
        else:
            with open(local_path, "rb") as f:
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
                        print(f"Uploaded {file_name}: 100.00%")
                    else:
                        chunk = f.read(CHUNK_SIZE)
                        dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = f.tell()
                        uploaded += len(chunk)
                        percent = (uploaded / file_size) * 100 if file_size else 0
                        print(f"Uploading {file_name}: {percent:.2f}%")
        # Optionally delete after upload:
        # os.remove(local_path)
    except Exception as e:
        print(f"Upload failed for {file_name}: {e}")

if __name__ == "__main__":
    file_name = input("Enter the file name present in temp_downloads folder: ").strip()
    local_path = os.path.join(TEMP_DIR, file_name)
    if os.path.exists(local_path):
        upload_file(local_path, file_name)
    else:
        print(f"File '{file_name}' not found in '{TEMP_DIR}'.")