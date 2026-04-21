import json
import os
import tempfile
from typing import List, Dict, Optional

DB_PATH = "/opt/trustpanel/data/users.json"


# -------------------------
# FILE INIT
# -------------------------
def _ensure_file():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


# -------------------------
# LOAD (SAFE)
# -------------------------
def load() -> List[Dict]:
    _ensure_file()

    try:
        with open(DB_PATH, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        # фильтрация битых записей
        clean = []
        for u in data:
            if isinstance(u, dict) and "username" in u:
                clean.append(u)

        return clean

    except json.JSONDecodeError:
        # файл повреждён → НЕ скрываем полностью, но не падаем
        return []

    except Exception:
        return []


# -------------------------
# SAVE (ATOMIC)
# -------------------------
def save(data: List[Dict]):
    _ensure_file()

    dir_name = os.path.dirname(DB_PATH)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, DB_PATH)


# -------------------------
# ADD USER
# -------------------------
def add_user(user: Dict):
    data = load()

    if "username" not in user:
        raise ValueError("username required")

    for u in data:
        if u.get("username") == user["username"]:
            raise ValueError("User already exists")

    # нормализация структуры
    safe_user = {
        "username": user["username"],
        "password": user.get("password", ""),
        "created_at": user.get("created_at", "now"),
        "expires_at": user.get("expires_at"),
        "status": user.get("status", "active")
    }

    data.append(safe_user)
    save(data)


# -------------------------
# DELETE USER
# -------------------------
def delete_user(username: str):
    data = load()

    new_data = [u for u in data if u.get("username") != username]

    if len(new_data) == len(data):
        raise ValueError("User not found")

    save(new_data)


# -------------------------
# UPDATE USER
# -------------------------
def update_user(username: str, **kwargs):
    data = load()

    found = False

    for user in data:
        if user.get("username") == username:
            user.update(kwargs)
            found = True
            break

    if not found:
        raise ValueError("User not found")

    save(data)


# -------------------------
# GET USER
# -------------------------
def get_user(username: str) -> Optional[Dict]:
    data = load()

    for user in data:
        if user.get("username") == username:
            return user

    return None


# -------------------------
# LIST USERS
# -------------------------
def list_users() -> List[Dict]:
    return load()