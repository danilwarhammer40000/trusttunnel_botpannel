import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# -------- STATES --------

class Register(StatesGroup):
    plan = State()
    username = State()


# -------- KEYBOARDS --------

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Подключить")],
        [KeyboardButton(text="🔄 Продлить")]
    ],
    resize_keyboard=True
)

plan_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="3 FREE")],
        [KeyboardButton(text="30 дней")],
        [KeyboardButton(text="60 дней")]
    ],
    resize_keyboard=True
)


# -------- START --------

from core.db import get_user_by_telegram_id

@dp.message(F.text == "/start")
async def start(msg: Message):
    user = get_user_by_telegram_id(msg.from_user.id)

    if not user:
        await msg.answer("Выберите действие:", reply_markup=start_kb)
    else:
        await msg.answer(
            f"Ваш аккаунт: {user['username']}\n"
            f"Истекает: {user.get('expires_at')}",
            reply_markup=start_kb
        )


# -------- CONNECT --------

@dp.message(F.text == "🚀 Подключить")
async def connect(msg: Message, state: FSMContext):
    user = get_user_by_telegram_id(msg.from_user.id)

    if user:
        await msg.answer("❌ У вас уже есть аккаунт")
        return

    await state.set_state(Register.plan)
    await msg.answer("Выберите тариф:", reply_markup=plan_kb)


# -------- PLAN --------

@dp.message(Register.plan)
async def choose_plan(msg: Message, state: FSMContext):
    text = msg.text

    if text == "3 FREE":
        plan = "trial"
        days = 3
    elif text == "30 дней":
        plan = "paid"
        days = 30
    elif text == "60 дней":
        plan = "paid"
        days = 60
    else:
        await msg.answer("Выбери кнопку")
        return

    await state.update_data(plan=plan, days=days)
    await state.set_state(Register.username)

    await msg.answer("Введите username (a-z0-9, 4-16):")


# -------- USERNAME --------

from services.users import create_user_safe, activate_trial, activate_paid, generate_password
from core.service import safe_sync

@dp.message(Register.username)
async def username_input(msg: Message, state: FSMContext):
    data = await state.get_data()

    try:
        password = generate_password()

        user = create_user_safe(
            tg_id=msg.from_user.id,
            username=msg.text,
            password=password,
            plan=data["plan"]
        )

        if data["plan"] == "trial":
            activate_trial(user["username"])
            safe_sync()

            await msg.answer(
                f"✅ FREE активирован\n"
                f"Логин: {user['username']}\n"
                f"Пароль: {password}"
            )

        else:
            await msg.answer("💳 Оплата пока не подключена")

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")
        return

    await state.clear()


# -------- MAIN --------

async def main():
    print("PUBLIC BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
