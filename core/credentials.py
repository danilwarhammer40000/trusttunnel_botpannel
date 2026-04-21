import toml
import shutil
import os
import tempfile

CREDENTIALS_PATH = "/opt/trusttunnel/credentials.toml"


# -------------------------
# LOAD SAFE
# -------------------------
def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        # вместо падения → создаём пустую структуру
        return {"client": []}

    try:
        data = toml.load(CREDENTIALS_PATH)

        if not isinstance(data, dict):
            return {"client": []}

        if "client" not in data:
            data["client"] = []

        return data

    except Exception:
        # битый toml → fallback
        return {"client": []}


# -------------------------
# ATOMIC SAVE
# -------------------------
def save_credentials(data):
    dir_name = os.path.dirname(CREDENTIALS_PATH)
    os.makedirs(dir_name, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name) as tmp:
        toml.dump(data, tmp)
        tmp_path = tmp.name

    os.replace(tmp_path, CREDENTIALS_PATH)


# -------------------------
# BACKUP
# -------------------------
def backup_credentials():
    if os.path.exists(CREDENTIALS_PATH):
        shutil.copy(
            CREDENTIALS_PATH,
            CREDENTIALS_PATH + ".bak"
        )


# -------------------------
# ADD USER
# -------------------------
def add_user_to_credentials(username, password):
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
    data = load_credentials()

    clients = data.get("client", [])

    new_clients = [
        c for c in clients
        if c.get("username") != username
    ]

    data["client"] = new_clients
    save_credentials(data)


# -------------------------
# REGENERATE USER
# -------------------------
def regenerate_user(username, password):
    remove_user_from_credentials(username)
    add_user_to_credentials(username, password)