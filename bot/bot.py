import asyncio
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from core.service import safe_sync
from core.generator import generate_link
from core.db import add_user, delete_user, list_users, get_user, update_user


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


class ExtendUser(StatesGroup):
    mode = State()
    manual = State()


# ---------------- KEYBOARD ----------------

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Add user")],
        [KeyboardButton(text="📋 List users")],
        [KeyboardButton(text="❌ Delete user")],
        [KeyboardButton(text="🔗 Get link")],
        [KeyboardButton(text="🔄 Sync users")]
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
    await msg.answer("TrustPanel online", reply_markup=main_menu)


# ---------------- CANCEL ----------------

@dp.message(F.text.lower() == "❌ cancel")
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Cancelled", reply_markup=ReplyKeyboardRemove())
    await msg.answer("Menu:", reply_markup=main_menu)


# ---------------- SYNC BUTTON ----------------

@dp.message(F.text == "🔄 Sync users")
async def sync_users(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return

    await msg.answer("🔄 Sync started...")

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, safe_sync)

        await msg.answer("✅ Sync completed")
    except Exception as e:
        await msg.answer(f"❌ Sync error: {str(e)}")


# ---------------- ADD USER FLOW ----------------

@dp.message(F.text == "➕ Add user")
async def menu_add(msg: Message, state: FSMContext):
    await state.set_state(AddUser.username)
    await msg.answer("Enter username:", reply_markup=cancel_kb)


@dp.message(AddUser.username)
async def add_username(msg: Message, state: FSMContext):
    await state.update_data(username=msg.text.strip())
    await state.set_state(AddUser.password)
    await msg.answer("Enter password:")


@dp.message(AddUser.password)
async def add_password(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text.strip())
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

    expires_at = None if days == 0 else (
        datetime.utcnow() + timedelta(days=days)
    ).strftime("%Y-%m-%d")

    add_user({
        "username": username,
        "password": password,
        "created_at": "now",
        "expires_at": expires_at,
        "status": "active"
    })

    safe_sync()

    link = generate_link(username, DOMAIN)

    await msg.answer(
        f"👤 Username: {username}\n"
        f"🔑 Password: {password}\n"
        f"⏳ Expires: {expires_at or '∞'}\n\n"
        f"🔗 {link}",
        reply_markup=ReplyKeyboardRemove()
    )

    await msg.answer("Menu:", reply_markup=main_menu)
    await state.clear()


# ---------------- LIST USERS ----------------

@dp.message(F.text == "📋 List users")
async def menu_list(msg: Message):
    users = list_users() or []

    if not users:
        await msg.answer("No users")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{u.get('username','?')} ({u.get('expires_at') or '∞'})",
            callback_data=f"extend:{u.get('username')}"
        )]
        for u in users if u.get("username")
    ])

    await msg.answer("Select user to extend:", reply_markup=kb)


# ---------------- EXTEND MENU ----------------

@dp.callback_query(F.data.startswith("extend:"))
async def extend_menu(call: CallbackQuery, state: FSMContext):
    username = call.data.split(":")[1]

    await state.update_data(username=username)
    await state.set_state(ExtendUser.mode)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ 3 days", callback_data="ext:3")],
        [InlineKeyboardButton(text="➕ 30 days", callback_data="ext:30")],
        [InlineKeyboardButton(text="∞ unlimited", callback_data="ext:0")],
        [InlineKeyboardButton(text="✍️ manual date", callback_data="ext:manual")]
    ])

    await call.message.answer(f"Extend user: {username}", reply_markup=kb)
    await call.answer()


# ---------------- EXTEND ----------------

@dp.callback_query(F.data.startswith("ext:"))
async def extend_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = data.get("username")

    mode = call.data.split(":")[1]

    user = get_user(username)
    if not user:
        await call.message.answer("User not found")
        return

    if mode == "0":
        update_user(username, expires_at=None, status="active")

    elif mode in ["3", "30"]:
        expires_at = (
            datetime.utcnow() + timedelta(days=int(mode))
        ).strftime("%Y-%m-%d")

        update_user(username, expires_at=expires_at, status="active")

    elif mode == "manual":
        await state.set_state(ExtendUser.manual)
        await call.message.answer("Send date YYYY-MM-DD")
        await call.answer()
        return

    safe_sync()

    await state.clear()
    await call.message.answer(f"Updated: {username}")
    await call.answer()


@dp.message(ExtendUser.manual)
async def manual_date(msg: Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("username")

    try:
        datetime.strptime(msg.text.strip(), "%Y-%m-%d")
    except:
        await msg.answer("Wrong format YYYY-MM-DD")
        return

    update_user(username, expires_at=msg.text.strip(), status="active")

    safe_sync()

    await state.clear()
    await msg.answer(f"Updated: {username}")


# ---------------- DELETE ----------------

@dp.message(F.text == "❌ Delete user")
async def menu_del(msg: Message):
    users = list_users() or []

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u.get("username"),
            callback_data=f"del:{u.get('username')}"
        )]
        for u in users if u.get("username")
    ])

    await msg.answer("Select user:", reply_markup=kb)


@dp.callback_query(F.data.startswith("del:"))
async def delete_callback(call: CallbackQuery):
    username = call.data.split(":")[1]

    delete_user(username)
    safe_sync()

    await call.message.answer(f"❌ Deleted: {username}")
    await call.answer()


# ---------------- LINK ----------------

@dp.message(F.text == "🔗 Get link")
async def menu_link(msg: Message):
    users = list_users() or []

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=u.get("username"),
            callback_data=f"link:{u.get('username')}"
        )]
        for u in users if u.get("username")
    ])

    await msg.answer("Select user:", reply_markup=kb)


@dp.callback_query(F.data.startswith("link:"))
async def link_callback(call: CallbackQuery):
    username = call.data.split(":")[1]

    user = get_user(username) or {}
    link = generate_link(username, DOMAIN)

    await call.message.answer(
        f"👤 Username: {username}\n"
        f"🔑 Password: {user.get('password')}\n"
        f"⏳ Expires: {user.get('expires_at') or '∞'}\n\n"
        f"🔗 {link}"
    )

    await call.answer()


# ---------------- MAIN ----------------

async def main():
    print("STARTING BOT...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
