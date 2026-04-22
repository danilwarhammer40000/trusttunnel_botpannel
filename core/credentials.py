import toml
import os
import tempfile
from datetime import datetime
from filelock import FileLock

CREDENTIALS_PATH = "/opt/trusttunnel/credentials.toml"
LOCK_PATH = "/opt/trusttunnel/credentials.lock"

lock = FileLock(LOCK_PATH, timeout=10)


def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        return {"client": []}

    try:
        data = toml.load(CREDENTIALS_PATH)
        if "client" not in data:
            data["client"] = []
        return data
    except Exception:
        return {"client": []}


def atomic_write(data):
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

    with lock:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(CREDENTIALS_PATH)) as tmp:
            toml.dump(data, tmp)
            tmp_path = tmp.name

        os.replace(tmp_path, CREDENTIALS_PATH)


# -------------------------
# 🔥 FULL REBUILD (MAIN FIX)
# -------------------------
def rebuild_credentials_from_db(users):
    """
    ВАЖНО:
    TOML = полностью пересобирается из JSON
    никаких incremental updates
    """

    clients = []

    for u in users:
        if u.get("status") != "active":
            continue

        clients.append({
            "username": u["username"],
            "password": u.get("password", "")
        })

    atomic_write({"client": clients})


def remove_user_from_credentials(username):
    data = load_credentials()

    data["client"] = [
        c for c in data.get("client", [])
        if c.get("username") != username
    ]

    atomic_write(data)
