from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.users import (
    create_user_safe,
    activate_trial,
    activate_paid,
    extend_user_safe,
    generate_password
)

from core.db import get_user, list_users

app = FastAPI()

print("🔥 TRUSTPANEL API LOADED")


# ================= MODELS =================

class CreateUserRequest(BaseModel):
    telegram_id: int
    username: str
    plan: str  # trial / paid


class ExtendRequest(BaseModel):
    username: str
    days: int


class ActivatePaidRequest(BaseModel):
    username: str
    days: int


# ================= USERS =================

@app.get("/users/list")
def users_list():
    return list_users()


@app.get("/users/{username}")
def user_detail(username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    return user


@app.post("/users/create")
def create_user(data: CreateUserRequest):
    try:
        password = generate_password()

        user = create_user_safe(
            tg_id=data.telegram_id,
            username=data.username,
            password=password,
            plan=data.plan
        )

        # trial активируем только тут
        if data.plan == "trial":
            activate_trial(user["username"])

        return {
            "username": user["username"],
            "password": password,
            "plan": user["plan"],
            "status": user["status"]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/paid")
def paid(data: ActivatePaidRequest):
    try:
        activate_paid(data.username, data.days)
        return {"status": "paid_activated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/extend")
def extend(data: ExtendRequest):
    try:
        extend_user_safe(data.username, data.days)
        return {"status": "extended"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
