import json
import os
import tempfile
from typing import List, Dict, Optional

DB_PATH = "/opt/trustpanel/data/users.json"


def _ensure():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            json.dump([], f)


def load() -> List[Dict]:
    _ensure()

    try:
        with open(DB_PATH, "r") as f:
            data = json.load(f)

        return [u for u in data if isinstance(u, dict)]
    except:
        return []


def save(data: List[Dict]):
    _ensure()

    with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(DB_PATH)) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, DB_PATH)


def list_users():
    return load()


def update_user(username: str, **kwargs):
    data = load()

    for u in data:
        if u.get("username") == username:
            u.update(kwargs)
            break

    save(data)
