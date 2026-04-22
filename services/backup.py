import os
import shutil
from datetime import datetime

CREDENTIALS = "/opt/trusttunnel/credentials.toml"
BACKUP_DIR = "/opt/trusttunnel/backups"

MAX_BACKUPS = 3


def run():
    if not os.path.exists(CREDENTIALS):
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"credentials.{ts}.bak")

    shutil.copy(CREDENTIALS, dst)

    # чистим старые
    files = sorted(os.listdir(BACKUP_DIR))

    if len(files) > MAX_BACKUPS:
        for f in files[:-MAX_BACKUPS]:
            os.remove(os.path.join(BACKUP_DIR, f))

    print(f"[BACKUP] Created: {dst}")


if __name__ == "__main__":
    run()
