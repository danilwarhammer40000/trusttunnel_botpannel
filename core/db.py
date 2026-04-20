import json
import os
import tempfile
from datetime import datetime

DB_PATH = "/opt/trustpanel/data/users.json"


def _ensure_file():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


def load():
    _ensure_file()
    try:
        with open(DB_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save(data):
    """Атомарная запись (через temp файл)"""
    _ensure_file()

    dir_name = os.path.dirname(DB_PATH)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, DB_PATH)


def add_user(user):
    data = load()

    # защита от дублей
    for u in data:
        if u["username"] == user["username"]:
            raise ValueError("User already exists")

    data.append(user)
    save(data)


def delete_user(username):
    data = load()
    data = [u for u in data if u["username"] != username]
    save(data)


def update_user(username, **kwargs):
    data = load()

    for user in data:
        if user["username"] == username:
            user.update(kwargs)
            break

    save(data)


def get_user(username):
    data = load()
    for user in data:
        if user["username"] == username:
            return user
    return None


def list_users():
    return load()