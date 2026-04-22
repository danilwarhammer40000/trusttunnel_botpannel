import sys
from datetime import datetime, timezone

sys.path.append("/opt/trustpanel")

from core.db import list_users, update_user
from core.service import safe_sync


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def run():
    users = list_users()
    now = datetime.now(timezone.utc)

    expired_users = []

    for u in users:
        if u.get("status") != "active":
            continue

        expires = u.get("expires_at")
        if not expires:
            continue

        exp_dt = parse_date(expires)
        if not exp_dt:
            continue

        if exp_dt < now:
            print(f"[CLEANUP] Expired: {u['username']}")
            expired_users.append(u["username"])

            update_user(u["username"], status="inactive")

    # 🔥 ВАЖНО: единый sync + reload (замена ручных операций)
    if expired_users:
        result = safe_sync()
        print(f"[CLEANUP] Sync result: {result}")


if __name__ == "__main__":
    run()
