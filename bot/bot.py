import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from core.service import safe_sync
from core.generator import generate_link
from core.db import add_user, delete_user, list_users, get_user
from core.credentials import remove_user_from_credentials


# ---------------- ENV ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DOMAIN = os.getenv("TRUSTTUNNEL_DOMAIN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")
if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID missing")
if not DOMAIN:
    raise RuntimeError("TRUSTTUNNEL_DOMAIN missing")


# ---------------- BOT ----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------- FSM ----------------

class AddUser(StatesGroup):
    username = State()
    password = State()
    days = State()


# ---------------- UI ----------------

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Add user", callback_data="menu:add")],
    [InlineKeyboardButton(text="📋 List users", callback_data="menu:list")],
    [InlineKeyboardButton(text="❌ Delete user", callback_data="menu:del")],
    [InlineKeyboardButton(text="🔗 Get link", callback_data="menu:link")]
])


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Cancel")]],
    resize_keyboard=True
)


# ---------------- START ----------------

@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("TrustPanel online", reply_markup=main_menu)


# ---------------- CANCEL ----------------

@dp.message(F.text.lower().in_(["cancel", "❌ cancel"]))
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Cancelled", reply_markup=main_menu)


# ---------------- MENU ----------------

@dp.callback_query(F.data.startswith("menu:"))
async def menu_router(call: CallbackQuery, state: FSMContext):
    action = call.data.split(":")[1]

    # ADD
    if action == "add":
        await state.set_state(AddUser.username)
        await call.message.answer("Enter username:", reply_markup=cancel_kb)

    # LIST
    elif action == "list":
        users = list_users()

        if not users:
            await call.message.answer("No users")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{u['username']} ({u.get('expires_at') or '∞'})",
                    callback_data=f"info:{u['username']}"
                )]
                for u in users
            ])

            await call.message.answer("Users:", reply_markup=kb)

    # DELETE
    elif action == "del":
        users = list_users()

        if not users:
            await call.message.answer("No users")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"del:{u['username']}"
                )]
                for u in users
            ])

            await call.message.answer("Select user:", reply_markup=kb)

    # LINK
    elif action == "link":
        users = list_users()

        if not users:
            await call.message.answer("No users")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=u["username"],
                    callback_data=f"link:{u['username']}"
                )]
                for u in users
            ])

            await call.message.answer("Select user:", reply_markup=kb)

    await call.answer()


# ---------------- ADD FLOW ----------------

@dp.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text)
    await state.set_state(AddUser.password)
    await msg.answer("Enter password:", reply_markup=cancel_kb)


@dp.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text)
    await state.set_state(AddUser.days)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="3")],
            [KeyboardButton(text="30")],
            [KeyboardButton(text="0")]
        ],
        resize_keyboard=True
    )

    await msg.answer("Select duration (days):", reply_markup=kb)


@dp.message(AddUser.days)
async def add_days(msg: Message, state: FSMContext):
    data = await state.get_data()

    username = data["username"]
    password = data["password"]

    try:
        days = int(msg.text.strip())
    except:
        await msg.answer("Use 3 / 30 / 0")
        return

    expires_at = None if days == 0 else days

    add_user({
        "username": username,
        "password": password,
        "created_at": "now",
        "expires_at": expires_at,
        "status": "active"
    })

    safe_sync()

    link = generate_link(username, DOMAIN)

    await msg.answer(f"✅ Created:\n\n{link}", reply_markup=main_menu)
    await state.clear()


# ---------------- INFO ----------------

@dp.callback_query(F.data.startswith("info:"))
async def info_user(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = get_user(username)

    if not user:
        await call.message.answer("User not found")
    else:
        await call.message.answer(
            f"👤 {username}\n"
            f"Expires: {user.get('expires_at') or '∞'}\n"
            f"Status: {user.get('status')}"
        )

    await call.answer()


# ---------------- DELETE ----------------

@dp.callback_query(F.data.startswith("del:"))
async def delete_callback(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)
    remove_user_from_credentials(username)

    safe_sync()

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()


# ---------------- LINK ----------------

@dp.callback_query(F.data.startswith("link:"))
async def link_callback(call: CallbackQuery):
    username = call.data.split(":")[1]

    link = generate_link(username, DOMAIN)

    await call.message.answer(f"🔗 {link}")
    await call.answer()


# ---------------- MAIN ----------------

async def main():
    print("STARTING BOT...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())