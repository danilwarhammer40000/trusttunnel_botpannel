import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.append("/opt/trustpanel")

from core.db import list_users, update_user
from core.service import full_resync_and_reload, mark_user_inactive


# -----------------------------
# Helpers
# -----------------------------

def parse_expiry(date_str: str) -> Optional[datetime]:
    """
    Safe ISO date parsing.
    Supports:
    - YYYY-MM-DD
    - full ISO format
    """
    if not date_str:
        return None

    try:
        # Fast path: full ISO (preferred)
        dt = datetime.fromisoformat(date_str)
    except Exception:
        try:
            # fallback legacy format
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return None

    # normalize timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


# -----------------------------
# Core logic
# -----------------------------

def run():
    users = list_users()
    now = datetime.now(timezone.utc)

    expired_users = []

    for u in users:
        if u.get("status") != "active":
            continue

        username = u.get("username")
        if not username:
            continue

        expires_raw = u.get("expires_at")
        exp_dt = parse_expiry(expires_raw)

        if not exp_dt:
            continue

        if exp_dt < now:
            expired_users.append(username)

    if not expired_users:
        print("[CLEANUP] No expired users found")
        return

    print(f"[CLEANUP] Expired users: {len(expired_users)}")

    changed = False

    for username in expired_users:
        try:
            print(f"[CLEANUP] DISABLING: {username}")

            mark_user_inactive(username)
            update_user(username, status="inactive")

            changed = True

        except Exception as e:
            print(f"[CLEANUP][ERROR] {username}: {e}")

    if changed:
        print("[CLEANUP] FULL RESYNC TRIGGERED")
        try:
            full_resync_and_reload()
        except Exception as e:
            print(f"[CLEANUP][ERROR] resync failed: {e}")
    else:
        print("[CLEANUP] No changes applied")


if __name__ == "__main__":
    run()
