import toml
import shutil
import os
import tempfile
from datetime import datetime
from filelock import FileLock

CREDENTIALS_PATH = "/opt/trusttunnel/credentials.toml"
LOCK_PATH = "/opt/trusttunnel/credentials.lock"


# -------------------------
# LOAD SAFE (READ ONLY)
# -------------------------
def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        return {"client": []}

    try:
        data = toml.load(CREDENTIALS_PATH)

        if not isinstance(data, dict):
            return {"client": []}

        if "client" not in data or not isinstance(data["client"], list):
            data["client"] = []

        return data

    except Exception as e:
        print(f"[ERROR] credentials.toml corrupted: {e}")
        return {"client": []}


# -------------------------
# ATOMIC SAVE (LOCKED)
# -------------------------
def save_credentials(data):
    os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

    with FileLock(LOCK_PATH):
        with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(CREDENTIALS_PATH)) as tmp:
            toml.dump(data, tmp)
            tmp_path = tmp.name

        os.replace(tmp_path, CREDENTIALS_PATH)


# -------------------------
# BACKUP (HISTORY SAFE)
# -------------------------
def backup_credentials():
    if os.path.exists(CREDENTIALS_PATH):
        os.makedirs(os.path.dirname(CREDENTIALS_PATH), exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        shutil.copy(
            CREDENTIALS_PATH,
            f"{CREDENTIALS_PATH}.{ts}.bak"
        )


# -------------------------
# ADD USER
# -------------------------
def add_user_to_credentials(username, password):
    with FileLock(LOCK_PATH):
        data = load_credentials()

        clients = data.get("client", [])

        for c in clients:
            if c.get("username") == username:
                raise ValueError("User already exists in credentials")

        clients.append({
            "username": username,
            "password": password
        })

        data["client"] = clients
        save_credentials(data)


# -------------------------
# REMOVE USER
# -------------------------
def remove_user_from_credentials(username):
    with FileLock(LOCK_PATH):
        data = load_credentials()

        clients = data.get("client", [])

        data["client"] = [
            c for c in clients
            if c.get("username") != username
        ]

        save_credentials(data)


# -------------------------
# REGENERATE USER
# -------------------------
def regenerate_user(username, password):
    with FileLock(LOCK_PATH):
        data = load_credentials()

        # remove old
        data["client"] = [
            c for c in data.get("client", [])
            if c.get("username") != username
        ]

        # add new
        data["client"].append({
            "username": username,
            "password": password
        })

        save_credentials(data)