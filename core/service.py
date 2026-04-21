import subprocess
from core.db import list_users
from core.credentials import (
    add_user_to_credentials,
    remove_user_from_credentials,
    load_credentials
)
from core.credentials import backup_credentials

TRUSTTUNNEL_SERVICE = "trusttunnel"


def restart_trusttunnel():
    subprocess.run(["systemctl", "restart", TRUSTTUNNEL_SERVICE])


def sync_db_to_credentials():
    """
    Главная синхронизация:
    DB → credentials.toml
    """

    db_users = list_users()
    creds = load_credentials()

    db_map = {u["username"]: u for u in db_users}
    cred_map = {c["username"]: c for c in creds.get("client", [])}

    # 🔹 1. Добавление / обновление
    for username, user in db_map.items():
        if user["status"] != "active":
            continue

        if username not in cred_map:
            add_user_to_credentials(username, user["password"])

    # 🔹 2. Удаление неактивных
    for username in list(cred_map.keys()):
        if username not in db_map or db_map[username]["status"] != "active":
            remove_user_from_credentials(username)


def safe_sync():
    """
    Безопасная синхронизация:
    backup → sync → restart
    """

    try:
        backup_credentials()
        sync_db_to_credentials()
        restart_trusttunnel()
        return "OK"

    except Exception as e:
        return f"ERROR: {str(e)}"


def force_reload_user(username):
    """
    Пересоздать конкретного пользователя
    """

    db_users = list_users()

    user = None
    for u in db_users:
        if u["username"] == username:
            user = u
            break

    if not user:
        raise ValueError("User not found in DB")

    backup_credentials()
    remove_user_from_credentials(username)

    if user["status"] == "active":
        add_user_to_credentials(username, user["password"])

    restart_trusttunnel()

