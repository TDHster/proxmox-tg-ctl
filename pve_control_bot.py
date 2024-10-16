import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')


# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Укажите ваш токен бота
ALLOWED_USER_ID = 104887251  # ID разрешенного пользователя

# Создаем объекты для работы с ботом
bot = Bot(token=API_TOKEN, session=AiohttpSession())
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Инлайн-кнопки
async def get_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Команда 1", callback_data="command_1")
    keyboard.button(text="Команда 2", callback_data="command_2")
    keyboard.button(text="Команда 3", callback_data="command_3")
    return keyboard.as_markup()

# Обработчик команды /start с проверкой ID пользователя
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    if message.from_user.id == ALLOWED_USER_ID:
        await message.answer("Добро пожаловать! Выберите команду:", reply_markup=await get_inline_keyboard())
    else:
        await message.answer("У вас нет доступа к этому боту.")

# Обработка нажатий на инлайн-кнопки
@router.callback_query(F.data.in_({"command_1", "command_2", "command_3"}))
async def process_callback_button(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ALLOWED_USER_ID:
        await callback_query.answer("У вас нет доступа к этой команде!", show_alert=True)
        return

    if callback_query.data == "command_1":
        await callback_query.message.answer("Вы выбрали Команду 1!")
    elif callback_query.data == "command_2":
        await callback_query.message.answer("Вы выбрали Команду 2!")
    elif callback_query.data == "command_3":
        await callback_query.message.answer("Вы выбрали Команду 3!")

    await callback_query.answer()


# Регистрация роутеров
dp.include_router(router)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())