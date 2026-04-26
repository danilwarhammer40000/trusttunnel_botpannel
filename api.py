from fastapi import FastAPI
from core.service import get_users, get_user_by_username

app = FastAPI()

@app.get("/users/list")
def users_list():
    return get_users()

@app.get("/users/{username}")
def user(username: str):
    return get_user_by_username(username)