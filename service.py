import subprocess
from core.db import list_users
from core.credentials import rebuild_credentials_from_db

TRUSTTUNNEL_SERVICE = "trusttunnel.service"


def restart_trusttunnel():
    result = subprocess.run(
        ["systemctl", "restart", TRUSTTUNNEL_SERVICE],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("[ERROR] trusttunnel restart failed:")
        print(result.stderr)
    else:
        print("[OK] trusttunnel restarted")


# ---------------- FULL SYNC ----------------

def full_resync_and_reload():
    users = list_users()
    rebuild_credentials_from_db(users)
    restart_trusttunnel()


def mark_user_inactive(username: str):
    # теперь просто логический маркер (файл пересоберётся при sync)
    pass


# ---------------- SAFE SYNC ----------------

def safe_sync():
    try:
        full_resync_and_reload()
        return "OK"
    except Exception as e:
        print("[SYNC ERROR]", str(e))
        return f"ERROR: {str(e)}"