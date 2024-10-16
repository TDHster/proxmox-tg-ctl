import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from proxmox import load_servers_config
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Укажите ID разрешенного пользователя
ALLOWED_USER_ID = 104887251  # Замените на нужный ID

# Создаем объекты для работы с ботом
bot = Bot(token=API_TOKEN, session=AiohttpSession())
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Инлайн-кнопки с динамическим созданием из конфигурации серверов
async def get_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    
    # Загружаем список серверов из конфигурации
    servers = load_servers_config()

    # Создаем кнопки для каждого сервера
    for server in servers['servers']:
        logging.info(f"Создание кнопки для сервера: {server['name']}, callback_data='pve_{server['name']}'")
        keyboard.button(text=server['name'], callback_data=f"pve_{server['name']}")  # Генерируем уникальный callback_data для каждого сервера
    
    return keyboard.as_markup()

# Обработчик команды /start с проверкой ID пользователя
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    if message.from_user.id == ALLOWED_USER_ID:
        await message.answer("Добро пожаловать! Выберите сервер:", reply_markup=await get_inline_keyboard())
    else:
        await message.answer("У вас нет доступа к этому боту.")

# Обработка нажатий на инлайн-кнопки (колбэки серверов)
@router.callback_query(F.data.startswith("pve_"))  # Фильтрация колбэков, начинающихся с "pve_"
async def process_server_callback(callback_query: types.CallbackQuery):
    # logging.info(f"Получен callback_data: {callback_query.data}")  # Логируем данные колбэка

    if callback_query.from_user.id != ALLOWED_USER_ID:
        await callback_query.answer("У вас нет доступа к этой команде!", show_alert=True)
        return

    # Извлекаем название сервера из callback_data
    server_name = callback_query.data[4:]  # Убираем префикс "pve_"

    # Получаем ID чата из callback_query.message и отправляем сообщение явно через bot.send_message
    chat_id = callback_query.message.chat.id

    await bot.send_message(chat_id, f"Вы выбрали сервер: {server_name}")

    await callback_query.answer()  # Это закрывает уведомление о колбэке

# Регистрация роутеров
dp.include_router(router)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
