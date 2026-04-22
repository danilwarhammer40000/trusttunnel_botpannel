import os
import shutil
from datetime import datetime, timezone

CREDENTIALS = "/opt/trusttunnel/credentials.toml"
BACKUP_DIR = "/opt/trusttunnel/backups"

MAX_BACKUPS = 3


def run():
    if not os.path.exists(CREDENTIALS):
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"credentials.{ts}.bak")

    shutil.copy(CREDENTIALS, dst)

    # чистим старые (по времени создания файлов)
    files = sorted(
        [
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
        ],
        key=os.path.getmtime
    )

    if len(files) > MAX_BACKUPS:
        for f in files[:-MAX_BACKUPS]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

    print(f"[BACKUP] Created: {dst}")


if __name__ == "__main__":
    run()
