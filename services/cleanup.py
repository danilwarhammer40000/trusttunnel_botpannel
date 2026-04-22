import sys
from datetime import datetime

sys.path.append("/opt/trustpanel")

from core.db import list_users, update_user
from core.credentials import remove_user_from_credentials
from core.service import restart_trusttunnel

def run():
    users = list_users()
    now = datetime.utcnow()

    changed = False

    for u in users:
        if u.get("status") != "active":
            continue

        expires = u.get("expires_at")

        if not expires:
            continue

        try:
            exp_dt = datetime.strptime(expires, "%Y-%m-%d")
        except:
            continue

        if exp_dt < now:
            print(f"[CLEANUP] Expired: {u['username']}")

            remove_user_from_credentials(u["username"])
            update_user(u["username"], status="inactive")

            changed = True

    if changed:
        restart_trusttunnel()
        print("[CLEANUP] Restarted trusttunnel")

if __name__ == "__main__":
    run()
