import asyncio
import json
import logging
import os
import sys
print("Hello, tg_bot!")

token = os.getenv("BOT_TOKEN", "default_token")
print(f"Using token: {token}")
print(f"Manager ID: {os.getenv('MANAGER_ID', 'not set')}")
if token == "default_token":
    print("Warning: Using default token, please set the BOT_TOKEN environment variable.")

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = int(os.getenv("MANAGER_ID"))

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔹 Кнопка 1", callback_data="btn_1")],
    [InlineKeyboardButton(text="🔹 Кнопка 2", callback_data="btn_2")],
    [InlineKeyboardButton(text="🔹 Кнопка 3", callback_data="btn_3")],
    [InlineKeyboardButton(text="🔹 Кнопка 4", callback_data="btn_4")],
    [InlineKeyboardButton(text="📞 Зʼєднати з менеджером", callback_data="connect_manager")]
])

active_chats = {}  # {user_id: manager_id}
manager_chats = {} # {manager_id: user_id} — з ким зараз спілкується менеджер

# Кнопка для користувача "З'єднати з менеджером"
connect_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Зʼєднати з менеджером", callback_data="connect_manager")]
        ]
    )

# Кнопки для менеджера: завершити чат та вибрати клієнта
def manager_keyboard(first_name: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Завершити діалог", callback_data=f"end_chat:{first_name}")]
    ]
)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        text=f"Привіт, {message.from_user.full_name}! Обери опцію нижче 👇",
        reply_markup=main_menu_keyboard
    )

# Обробник команди старт (показує кнопку підключення)
# @dp.message(F.text == "/start")
# async def start_handler(message: Message):
#     await message.answer("Привіт!\nЦе головне меню. Ви можете натиснути кнопку нижче, щоб зв’язатись з менеджером.", reply_markup=main_menu_keyboard)

# Користувач натискає кнопку з'єднання
@dp.callback_query(F.data == "connect_manager")
async def connect_to_manager(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if user_id in active_chats:
        await callback.answer("Ви вже підключені до менеджера.")
        return
    
    active_chats[user_id] = MANAGER_ID
    manager_chats[MANAGER_ID] = user_id  # припустимо менеджер зараз спілкується з цим користувачем
    # Повідомлення менеджеру
    await bot.send_message(
        chat_id=MANAGER_ID,
        text=f"👤 Користувач {callback.from_user.first_name} (id: {callback.from_user.id}) хоче зʼєднатись з вами.\nВідповідайте прямо в чат, щоб відповісти.",
        reply_markup=manager_keyboard(callback.from_user.first_name)
    )
    await callback.message.answer("Ви з'єднані з менеджером. Всі ваші повідомлення будуть пересилатись менеджеру.")
    await callback.answer()

# Менеджер відповідає користувачу
@dp.message(F.from_user.id == MANAGER_ID)
async def manager_message_handler(message: Message, bot: Bot):
    manager_id = message.from_user.id
    if manager_id not in manager_chats:
        await message.answer("Ви зараз не спілкуєтесь з користувачем.")
        return
    
    user_id = manager_chats[manager_id]
    try:
        await bot.send_message(user_id, f"Менеджер: {message.text}")
    except Exception as e:
        await message.answer(f"Не вдалося відправити повідомлення користувачу: {e}")


# Користувач надсилає повідомлення — пересилаємо менеджеру
@dp.message()
async def user_message_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    if user_id not in active_chats:
        await message.answer("Натисніть кнопку 'З'єднати з менеджером', щоб почати чат.", reply_markup=connect_keyboard)
        return
    
    manager_id = active_chats[user_id]
    user = message.from_user
    print(f"User {user_id} ({user.full_name}) sent a message: {message.text}")
    # Відправляємо повідомлення менеджеру з кнопкою "Завершити"
    await bot.send_message(
        manager_id,
        f"Повідомлення від {message.from_user.full_name} (id: {user_id}):\n{message.text}",
        reply_markup=manager_keyboard(user.first_name)
    )

# Менеджер натискає кнопку "Завершити діалог"
@dp.callback_query(F.data.startswith("end_chat:"))
async def end_chat(callback: CallbackQuery, bot: Bot):
    print("Callback received:", callback)
    print("Start get text from callback message")
    text = callback.message.text.split("\n")[0]  # "end_chat:<user_id>"
    id = text.split(")")[0].split()[-1]  # Отримуємо ID користувача з тексту
    print("End get text from callback message")
    print("Callback id:", id)
    user_id = int(id)
    print("User ID from callback:", user_id)
    manager_id = callback.from_user.id
    
    if user_id in active_chats:
        del active_chats[user_id]
    if manager_id in manager_chats:
        del manager_chats[manager_id]
    
    await callback.message.answer("Діалог завершено.")
    await callback.answer()
    
    # Повідомити користувача про завершення
    try:
        await bot.send_message(user_id, "Менеджер завершив діалог.")
    except Exception as e:
        print(f"Не вдалося повідомити користувача: {e}")



@dp.message()
async def echo_handler(message: Message) -> None:
    print("Message echo User:", message.from_user)
    print(type(message))

    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        # Or you can use `send_copy
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
