import sys
from datetime import datetime, timezone

sys.path.append("/opt/trustpanel")

from core.db import list_users, update_user
from core.credentials import remove_user_from_credentials
from core.service import restart_trusttunnel


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
        except Exception:
            continue

        # приводим к timezone-safe сравнению
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

        if exp_dt < now:
            print(f"[CLEANUP] Expired: {u['username']}")

            try:
                remove_user_from_credentials(u["username"])
            except Exception as e:
                print(f"[CLEANUP] credentials error: {e}")

            update_user(u["username"], status="inactive")

            changed = True

    if changed:
        try:
            restart_trusttunnel()
            print("[CLEANUP] Restarted trusttunnel")
        except Exception as e:
            print(f"[CLEANUP] restart failed: {e}")


if __name__ == "__main__":
    run()
