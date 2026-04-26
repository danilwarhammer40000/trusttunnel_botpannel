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

    # проверка через список (единый источник истины)
    for u in list_users():
        if u.get("username") == username:
            raise ValueError("USERNAME_TAKEN")

    return username


# ================= CREATE USER =================

def create_user_safe(tg_id: int, username: str, password: str, plan: str):
    # 1 Telegram = 1 user
    if get_user_by_telegram_id(tg_id):
        raise ValueError("USER_ALREADY_EXISTS")

    username = validate_username(username)

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


# ================= TRIAL =================

def activate_trial(username: str):
    expires = datetime.utcnow() + timedelta(days=3)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active",
        trial_used=True
    )


# ================= PAID =================

def activate_paid(username: str, days: int):
    expires = datetime.utcnow() + timedelta(days=days)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active"
    )


# ================= EXTEND =================

def extend_user_safe(username: str, days: int):
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    now = datetime.utcnow()

    if user.get("expires_at"):
        current = datetime.strptime(user["expires_at"], "%Y-%m-%d")
        new_exp = current if current > now else now
        new_exp = new_exp + timedelta(days=days)
    else:
        new_exp = now + timedelta(days=days)

    update_user(
        username,
        expires_at=new_exp.strftime("%Y-%m-%d"),
        status="active"
    )
