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

    clients = []

    try:
        with open(CREDENTIALS_PATH, "r") as f:
            current = {}

            for line in f:
                line = line.strip()

                if line == "[[client]]":
                    if current:
                        clients.append(current)
                    current = {}

                elif line.startswith("username"):
                    current["username"] = line.split("=", 1)[1].strip().strip('"')

                elif line.startswith("password"):
                    current["password"] = line.split("=", 1)[1].strip().strip('"')

            if current:
                clients.append(current)

        return {"client": clients}

    except Exception:
        return {"client": []}


def atomic_write(data):
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

    with lock:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(CREDENTIALS_PATH)) as tmp:

            for client in data.get("client", []):
                tmp.write("[[client]]\n")
                tmp.write(f'username = "{client["username"]}"\n')
                tmp.write(f'password = "{client["password"]}"\n\n')

            tmp_path = tmp.name

        os.replace(tmp_path, CREDENTIALS_PATH)


# -------------------------
# FULL REBUILD
# -------------------------
def rebuild_credentials_from_db(users):
    clients = []

    now = datetime.utcnow()

    for u in users:
        if u.get("status") != "active":
            continue

        # expiration check
        exp = u.get("expires_at")
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                if exp_dt < now:
                    continue
            except Exception:
                continue

        username = u.get("username")
        password = u.get("password")

        if not username or not password:
            continue

        clients.append({
            "username": username,
            "password": password
        })

    atomic_write({"client": clients})


def remove_user_from_credentials(username):
    data = load_credentials()

    data["client"] = [
        c for c in data.get("client", [])
        if c.get("username") != username
    ]

    atomic_write(data)