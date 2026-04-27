from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os
import secrets
import string

DATA_FILE = "/opt/trustpanel/data/users.json"

app = FastAPI()


# ================= UTIL =================

def load_users():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)


def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))


# ================= MODELS =================

class CreateUser(BaseModel):
    telegram_id: int | None = None
    username: str
    plan: str


# ================= ROUTES =================

@app.get("/users/list")
def list_users():
    return load_users()


@app.get("/users/get/{username}")
def get_user(username: str):
    for u in load_users():
        if u["username"] == username:
            return u
    raise HTTPException(status_code=404, detail="USER_NOT_FOUND")


@app.post("/users/create")
def create_user(data: CreateUser):
    users = load_users()

    # check duplicate
    for u in users:
        if u["username"] == data.username:
            raise HTTPException(status_code=400, detail="USERNAME_TAKEN")

    user = {
        "username": data.username,
        "password": generate_password(),
        "telegram_id": data.telegram_id,
        "plan": data.plan,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (
            (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
            if data.plan == "trial"
            else None
        ),
        "trial_used": data.plan == "trial"
    }

    users.append(user)
    save_users(users)

    return user


@app.post("/users/update/{username}")
def update_user(username: str, payload: dict):
    users = load_users()

    for u in users:
        if u["username"] == username:
            u.update(payload)
            save_users(users)
            return u

    raise HTTPException(status_code=404, detail="USER_NOT_FOUND")


@app.get("/health")
def health():
    return {"status": "ok"}