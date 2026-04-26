from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.users import (
    create_user_safe,
    activate_trial,
    activate_paid,
    extend_user_safe
)

from core.db import get_user, get_all_users

app = FastAPI()


# ===== MODELS =====

class CreateUserRequest(BaseModel):
    telegram_id: int
    username: str
    password: str
    plan: str


class ExtendRequest(BaseModel):
    username: str
    days: int


class ActivatePaidRequest(BaseModel):
    username: str
    days: int


# ===== ENDPOINTS =====

@app.get("/users/list")
def users_list():
    return get_all_users()


@app.get("/users/{username}")
def user_detail(username: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    return user


@app.post("/users/create")
def create_user(data: CreateUserRequest):
    try:
        user = create_user_safe(
            tg_id=data.telegram_id,
            username=data.username,
            password=data.password,
            plan=data.plan
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/trial")
def trial(username: str):
    try:
        activate_trial(username)
        return {"status": "trial_activated"}
    except Exception as e:
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