
import asyncio
import logging
import os
import sys
print("Hello, tg_bot!")

token = os.getenv("BOT_TOKEN", "default_token")
print(f"Using token: {token}")
print(f"Manager ID: {os.getenv('MANAGER_ID', 'not set')}")
if token == "default_token":
    print("Warning: Using default token, please set the BOT_TOKEN environment variable.")

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

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


pending_requests = {}  # user_id: [list of messages]
active_chats = {}      # manager_id: user_id
last_message_ids = {}  # To track the last message ID for each user

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

def manager_end_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔚 Завершити діалог")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Завершити діалог..."
    )

def manager_find_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показати активні запити")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Надішліть повідомлення користувачу..."
    )

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user.id == MANAGER_ID:
        await message.answer(
            text=f"Привіт, {message.from_user.full_name}! Тут можна керувати запитами користувачів.",
            reply_markup=manager_find_keyboard()
        )
        return
    new_message = await message.answer(
        text=f"Привіт, {message.from_user.full_name}! Обери опцію нижче 👇",
        reply_markup=main_menu_keyboard
    )
    last_message_ids[message.from_user.id] = new_message.message_id



@dp.message(F.text == "Показати активні запити")
async def show_pending_users(message: Message):
    if message.from_user.id != MANAGER_ID:
        await message.answer("Це доступно лише менеджеру.")
        return
    if not pending_requests:
        await message.answer("Немає активних запитів.")
        return
    
    users = list()
    for uid in pending_requests:
        user = await message.bot.get_chat(uid)
        if user:
            users.append(user)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Почати діалог з {user.first_name}", 
                    callback_data=f"take_{user.id}"
                    )
            ]
            for user in users
        ]
    )
    await message.answer("Користувачі, які очікують:", reply_markup=keyboard)


@dp.callback_query(F.data == "connect_manager")
async def connect_to_manager(callback: CallbackQuery):
    user_id = callback.from_user.id
    first_name = callback.from_user.first_name
    pending_requests[user_id] = list()
    await callback.message.answer("Очікуйте зʼєднання з менеджером. Напишіть своє питання.")
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Відповісти користувачу {first_name}", 
                    callback_data=f"take_{user_id}"
                    )
            ]
        ]
    )
    await callback.bot.send_message(
        chat_id=MANAGER_ID,
        text=f"👤 Користувач {first_name} (id: {user_id}) надіслав запит.",
        reply_markup=keyboard
    )

@dp.message(F.text == "🔚 Завершити діалог")
async def end_chat_handler(message: Message):
    manager_id = message.from_user.id
    if manager_id in active_chats:
        user_id = active_chats.pop(manager_id)
        await message.answer("Діалог завершено.", reply_markup=manager_find_keyboard())
        await message.bot.send_message(
            user_id, 
            "Менеджер завершив діалог. Дякуємо!", 
            reply_markup=main_menu_keyboard
        )
    else:
        await message.answer("У вас немає активного діалогу.")


@dp.message()
async def message_router(message: Message):
    user_id = message.from_user.id

    # 1. Якщо це користувач, який очікує
    if user_id in pending_requests:
        pending_requests[user_id].append(message.text)

    # 2. Якщо це менеджер у чаті з юзером
    elif user_id in active_chats:
        target_user = active_chats[user_id]
        await message.bot.send_message(target_user, message.text)

    # 3. Якщо це юзер, з яким зараз говорить менеджер
    elif user_id in active_chats.values():
        for manager_id, uid in active_chats.items():
            if uid == user_id:
                await message.bot.send_message(manager_id, f"[{message.from_user.full_name}] {message.text}")
                break
    
    elif user_id == MANAGER_ID:
        last_message_id = last_message_ids.get(user_id, None)
        if last_message_id:
            try:
                await message.bot.delete_message(chat_id=user_id, message_id=last_message_id)
            except Exception as e:
                logging.error(f"Failed to delete last message: {e}")

        new_manager_message = await message.answer("Не можна надсилати повідомлення самому собі :).")
        last_message_ids[user_id] = new_manager_message.message_id
        return

    # 4. Інакше — інструкція
    else:
        last_message_id = last_message_ids.get(user_id, None)
        if last_message_id:
            try:
                await message.bot.delete_message(chat_id=user_id, message_id=last_message_id)
            except Exception as e:
                logging.error(f"Failed to delete last message: {e}")
        
        new_message = await message.answer(
            "Оберіть опцію нижче 👇\n Або натисніть кнопку «Зʼєднатись з менеджером», щоб отримати консультацію", 
            reply_markup=main_menu_keyboard
        )
        last_message_ids[user_id] = new_message.message_id


@dp.callback_query(F.data.startswith("take_"))
async def take_user(callback: CallbackQuery):
    manager_id = callback.from_user.id
    user_id = int(callback.data.split("_")[1])
    user = await callback.bot.get_chat(user_id)
    active_chats[manager_id] = user_id
    await callback.message.answer(
        f"Ви підʼєднались до користувача {user.first_name}.",
        reply_markup=manager_end_keyboard()
    )

    # Надіслати користувачу повідомлення
    await callback.bot.send_message(user_id, "Менеджер приєднався до чату.")

    # Надіслати попередні повідомлення
    for msg in pending_requests[user_id]:
        await callback.message.answer(f"[{user.first_name}] {msg}")

    del pending_requests[user_id]
    await callback.answer()









async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())