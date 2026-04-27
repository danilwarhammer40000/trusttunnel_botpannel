import re
import secrets
import string
from datetime import datetime, timedelta

from core.db import (
    add_user,
    get_user,
    update_user,
    get_user_by_telegram_id,
    list_users
)

from service import rebuild_credentials
from generator import generate_tt_link


USERNAME_RE = re.compile(r"^[a-z0-9]{4,16}$")


# ================= PASSWORD =================

def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))


# ================= VALIDATION =================

def validate_username(username: str):
    username = username.lower().strip()

    if not USERNAME_RE.match(username):
        raise ValueError("INVALID_USERNAME")

    for u in list_users():
        if u.get("username") == username:
            raise ValueError("USERNAME_TAKEN")

    return username


# ================= CREATE USER =================

def create_user_safe(tg_id: int, username: str, plan: str):
    existing = get_user_by_telegram_id(tg_id)

    if existing:
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

    add_user(user)

    return user


# ================= ACTIVATE TRIAL =================

def activate_trial(username: str):
    user = get_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    if user.get("trial_used"):
        raise ValueError("TRIAL_ALREADY_USED")

    expires = datetime.utcnow() + timedelta(days=3)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active",
        trial_used=True
    )

    rebuild_credentials()

    tt_link = generate_tt_link(user["username"], user["password"])

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": expires.strftime("%Y-%m-%d"),
        "tt_link": tt_link
    }


# ================= ACTIVATE PAID =================

def activate_paid(username: str, days: int):
    user = get_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    expires = datetime.utcnow() + timedelta(days=days)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active"
    )

    rebuild_credentials()

    tt_link = generate_tt_link(user["username"], user["password"])

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": expires.strftime("%Y-%m-%d"),
        "tt_link": tt_link
    }


# ================= EXTEND =================

def extend_user_safe(username: str, days: int):
    user = get_user(username)

    if not user:
        raise ValueError("USER_NOT_FOUND")

    now = datetime.utcnow()

    if user.get("expires_at"):
        current = datetime.strptime(user["expires_at"], "%Y-%m-%d")
        base = current if current > now else now
    else:
        base = now

    new_exp = base + timedelta(days=days)

    update_user(
        username,
        expires_at=new_exp.strftime("%Y-%m-%d"),
        status="active"
    )

    rebuild_credentials()

    tt_link = generate_tt_link(user["username"], user["password"])

    return {
        "username": user["username"],
        "password": user["password"],
        "expires_at": new_exp.strftime("%Y-%m-%d"),
        "tt_link": tt_link
    }