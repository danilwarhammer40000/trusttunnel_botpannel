import toml
import shutil
import os

CREDENTIALS_PATH = "/opt/trusttunnel/credentials.toml"


def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError("credentials.toml not found")

    return toml.load(CREDENTIALS_PATH)


def save_credentials(data):
    """Сохраняем аккуратно"""
    with open(CREDENTIALS_PATH, "w") as f:
        toml.dump(data, f)


def backup_credentials():
    """Простой backup (основная логика будет в services)"""
    if os.path.exists(CREDENTIALS_PATH):
        shutil.copy(CREDENTIALS_PATH, CREDENTIALS_PATH + ".bak")


def add_user_to_credentials(username, password):
    data = load_credentials()

    clients = data.get("client", [])

    # защита от дублей
    for c in clients:
        if c["username"] == username:
            raise ValueError("User already exists in credentials")

    clients.append({
        "username": username,
        "password": password
    })

    data["client"] = clients
    save_credentials(data)


def remove_user_from_credentials(username):
    data = load_credentials()

    clients = data.get("client", [])
    new_clients = [c for c in clients if c["username"] != username]

    data["client"] = new_clients
    save_credentials(data)


def regenerate_user(username, password):
    """Удалить и добавить заново"""
    remove_user_from_credentials(username)
    add_user_to_credentials(username, password)