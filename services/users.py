import re
from datetime import datetime, timedelta

from core.db import (
    add_user,
    get_user,
    update_user,
    get_user_by_telegram_id,
    username_exists
)

USERNAME_RE = re.compile(r"^[a-z0-9]{4,16}$")


def validate_username(username: str):
    username = username.lower().strip()

    if not USERNAME_RE.match(username):
        raise ValueError("INVALID_USERNAME")

    if username_exists(username):
        raise ValueError("USERNAME_TAKEN")

    return username


def create_user_safe(tg_id: int, username: str, password: str, plan: str):
    # 1 user = 1 telegram
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


def activate_trial(username: str):
    expires = datetime.utcnow() + timedelta(days=3)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active",
        trial_used=True
    )


def activate_paid(username: str, days: int):
    expires = datetime.utcnow() + timedelta(days=days)

    update_user(
        username,
        expires_at=expires.strftime("%Y-%m-%d"),
        status="active"
    )


def extend_user_safe(username: str, days: int):
    user = get_user(username)
    if not user:
        raise ValueError("USER_NOT_FOUND")

    now = datetime.utcnow()

    if user.get("expires_at"):
        current = datetime.strptime(user["expires_at"], "%Y-%m-%d")
        if current > now:
            new_exp = current + timedelta(days=days)
        else:
            new_exp = now + timedelta(days=days)
    else:
        new_exp = None

    update_user(
        username,
        expires_at=new_exp.strftime("%Y-%m-%d") if new_exp else None,
        status="active"
    )
