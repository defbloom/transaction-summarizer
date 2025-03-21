import os
import time
from datetime import datetime, timedelta

# Function to delete files older than 24 hours
def cleanup_upload_folder(upload_folder):
    while True:
        now = datetime.now()
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_mod_time > timedelta(hours=24):
                    try:
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path} at {datetime.now()}.\n")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}.\n")
        time.sleep(3600)  # Run cleanup every hour
