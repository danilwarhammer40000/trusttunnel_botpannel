import sys
from datetime import datetime, timezone

sys.path.append("/opt/trustpanel")

from core.db import list_users, update_user
from core.service import full_resync_and_reload, mark_user_inactive


def run():
    users = list_users()
    now = datetime.now(timezone.utc)

    changed = False

    for u in users:
        if u.get("status") != "active":
            continue

        expires = u.get("expires_at")
        if not expires:
            continue

        try:
            exp_dt = datetime.strptime(expires, "%Y-%m-%d")
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        except:
            continue

        if exp_dt < now:
            username = u["username"]
            print(f"[CLEANUP] EXPIRED: {username}")

            mark_user_inactive(username)
            update_user(username, status="inactive")

            changed = True

    if changed:
        print("[CLEANUP] FULL RESYNC")
        full_resync_and_reload()


if __name__ == "__main__":
    run()
