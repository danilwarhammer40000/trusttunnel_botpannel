import subprocess
from core.db import list_users
from core.credentials import rebuild_credentials_from_db, remove_user_from_credentials

TRUSTTUNNEL_SERVICE = "trusttunnel"


def restart_trusttunnel():
    subprocess.run(["systemctl", "restart", TRUSTTUNNEL_SERVICE])


# ---------------- FULL SYNC ----------------

def full_resync_and_reload():
    users = list_users()
    rebuild_credentials_from_db(users)
    restart_trusttunnel()


def mark_user_inactive(username: str):
    remove_user_from_credentials(username)


# ---------------- FIXED SAFE SYNC ----------------

def safe_sync():
    """
    DB → TOML → restart
    """
    try:
        full_resync_and_reload()
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"
