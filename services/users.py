import re
import secrets
import string
import json
import os
from datetime import datetime, timedelta

from core.service import rebuild_credentials
from trustpanel.generator import generate_tt_link


USERS_DB = "/opt/trustpanel/data/users.json"

USERNAME_RE = re.compile(r"^[a-z0-9]{4,16}$")


# ================= STORAGE =================

def load_users():
    if not os.path.exists(USERS_DB):
        return []
    with open(USERS_DB, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_DB, "w") as f:
        json.dump(users, f, indent=2)


def find_user(username: str):
    for u in load_users():
        if u.get("username") == username:
            return u
    return None


def find_by_tg(tg_id: int):
    for u in load_users():
        if u.get("telegram_id") == tg_id:
            return u
    return None


# ================= PASSWORD =================

def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))


# ================= VALIDATION =================

def validate_username(username: str):
    username = username.lower().strip()

    if not USERNAME_RE.match(username):
        raise ValueError("INVALID_USERNAME")

    if find_user(username):
        raise ValueError("USERNAME_TAKEN")

    return username


# ================= CREATE USER =================

def create_user_safe(tg_id: int, username: str, plan: str):
    if find_by_tg(tg_id):
        raise ValueError("USER_ALREADY_EXISTS")

    username = validate_username(username)
    password = generate_password()

    user = {
        "username": username,
        "password": password,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": None,
        "status": "inactive",
        "telegram_id": tg_id,
        "plan": plan,
        "trial_used": False
    }

    users = load_users()
    users.append(user)
    save_users(users)

    rebuild_credentials()

    return user


# ================= ACTIVATE TRIAL =================

def activate_trial(username: str):
    users = load_users()
    user = find_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    if user.get("trial_used"):
        raise ValueError("TRIAL_ALREADY_USED")

    expires = datetime.utcnow() + timedelta(days=3)

    user["expires_at"] = expires.strftime("%Y-%m-%d")
    user["status"] = "active"
    user["trial_used"] = True

    save_users(users)

    rebuild_credentials()

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": user["expires_at"],
        "tt_link": generate_tt_link(user["username"], user["password"])
    }


# ================= ACTIVATE PAID =================

def activate_paid(username: str, days: int):
    users = load_users()
    user = find_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    expires = datetime.utcnow() + timedelta(days=days)

    user["expires_at"] = expires.strftime("%Y-%m-%d")
    user["status"] = "active"

    save_users(users)

    rebuild_credentials()

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": user["expires_at"],
        "tt_link": generate_tt_link(user["username"], user["password"])
    }


# ================= EXTEND =================

def extend_user_safe(username: str, days: int):
    users = load_users()
    user = find_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    now = datetime.utcnow()

    if user.get("expires_at"):
        current = datetime.strptime(user["expires_at"], "%Y-%m-%d")
        base = current if current > now else now
    else:
        base = now

    new_exp = base + timedelta(days=days)

    user["expires_at"] = new_exp.strftime("%Y-%m-%d")
    user["status"] = "active"

    save_users(users)

    rebuild_credentials()

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": user["expires_at"],
        "tt_link": generate_tt_link(user["username"], user["password"])
    }