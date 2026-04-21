print("FILE LOADED")
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID missing in .env")


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from core.service import safe_sync
from core.generator import generate_link
from core.db import add_user, delete_user, list_users, update_user




# ---------------- FSM ----------------

class AddUser(StatesGroup):
    username = State()
    password = State()
    days = State()


# ---------------- BOT ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------- KEYBOARD ----------------

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ADD"), KeyboardButton(text="DEL")],
        [KeyboardButton(text="LINK"), KeyboardButton(text="LIST")]
    ],
    resize_keyboard=True
)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Cancel")]],
    resize_keyboard=True
)


# ---------------- START ----------------

@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("TrustPanel online", reply_markup=main_kb)


# ---------------- CANCEL ----------------

@dp.message(F.text == "❌ Cancel")
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Cancelled", reply_markup=main_kb)


# ---------------- ADD FLOW ----------------

@dp.message(F.text == "ADD")
async def add_start(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Username:", reply_markup=cancel_kb)


@dp.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text)
    await state.set_state(AddUser.password)
    await msg.answer("Password:")


@dp.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text)
    await state.set_state(AddUser.days)
    await msg.answer("Days (3 / 30 / 0 = unlimited):")


@dp.message(AddUser.days)
async def add_days(msg: Message, state: FSMContext):
    data = await state.get_data()

    username = data["username"]
    password = data["password"]
    days = int(msg.text)

    expires_at = None if days == 0 else days

    add_user({
        "username": username,
        "password": password,
        "created_at": "now",
        "expires_at": expires_at,
        "status": "active"
    })

    safe_sync()

    link = generate_link(username, "example.ru")

    await msg.answer(f"Created:\n\n{link}")

    await state.clear()


# ---------------- LIST ----------------

@dp.message(F.text == "LIST")
async def list_users_handler(msg: Message):
    users = list_users()

    if not users:
        await msg.answer("No users")
        return

    text = ""

    for u in users:
        status = "inactive" if u["status"] != "active" else ""
        exp = u["expires_at"] if u["expires_at"] else "∞"

        text += f"{u['username']} ({exp}) {status}\n"

    await msg.answer(text)


# ---------------- DEL ----------------
@dp.message(F.text == "DEL")
async def del_user(msg: Message):
    users = list_users()

    if not users:
        await msg.answer("No users")
        return

    kb = []

    for u in users:
        kb.append([
            InlineKeyboardButton(
                text=f"{u['username']} ({u['status']})",
                callback_data=f"del:{u['username']}"
            )
        ])

    await msg.answer(
        "Select user to delete:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    
    from core.credentials import remove_user_from_credentials
from core.service import safe_sync


@dp.callback_query(F.data.startswith("del:"))
async def delete_callback(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)
    remove_user_from_credentials(username)

    safe_sync()

    await call.message.answer(f"Deleted: {username}")
    await call.answer()
    
async def main():
    print("STARTING BOT...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

print("BOTTOM OF FILE REACHED")