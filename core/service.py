import subprocess
from core.db import list_users
from core.credentials import (
    rebuild_credentials_from_db,
    remove_user_from_credentials
)

TRUSTTUNNEL_SERVICE = "trusttunnel"


def restart_trusttunnel():
    """
    HARD RESTART (not soft restart)
    """
    subprocess.run(["systemctl", "restart", TRUSTTUNNEL_SERVICE])


# -------------------------
# FULL CONSISTENCY ENGINE
# -------------------------
def full_resync_and_reload():
    """
    DB → TOML (FULL REBUILD) → RESTART
    """

    users = list_users()

    rebuild_credentials_from_db(users)
    restart_trusttunnel()


def mark_user_inactive(username: str):
    """
    HARD KILL USER ACCESS IMMEDIATELY
    """

    remove_user_from_credentials(username)
