import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from proxmox import load_servers_config, get_server_by_name, ProxMox
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
async def get_pves_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    # Создаем кнопки для каждого сервера
    for server in pve_servers_config['servers']:
        # logging.info(f"Создание кнопки для сервера: {server['name']}, callback_data='pve_{server['name']}'")
        keyboard.button(text=server['name'], callback_data=f"pve_{server['name']}")  # Генерируем уникальный callback_data для каждого сервера
    
    return keyboard.as_markup()


# Обработчик команды /start с проверкой ID пользователя
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    if message.from_user.id == ALLOWED_USER_ID:
        await message.answer("Добро пожаловать! Выберите сервер:", reply_markup=await get_pves_inline_keyboard())
    else:
        await message.answer("У вас нет доступа к этому боту.")


# Обработка нажатий на инлайн-кнопки (колбэки серверов)
@router.callback_query(F.data.startswith("pve_"))  # Фильтрация колбэков, начинающихся с "pve_"
async def process_pveserver_callback(callback_query: types.CallbackQuery):
    # logging.info(f"Получен callback_data: {callback_query.data}")  # Логируем данные колбэка

    if callback_query.from_user.id != ALLOWED_USER_ID:
        await callback_query.answer("У вас нет доступа к этой команде!", show_alert=True)
        return

    # Извлекаем название сервера из callback_data
    server_name = callback_query.data[4:]  # Убираем префикс "pve_"

    # Получаем ID чата из callback_query.message и отправляем сообщение явно через bot.send_message
    chat_id = callback_query.message.chat.id
    await bot.send_message(chat_id, f"Получаю список vm с сервера: {server_name}")
    await callback_query.answer()  # Это закрывает уведомление о колбэке
    await pveserver_selected(server_name, chat_id=chat_id)


async def pveserver_selected(pve_server_name, chat_id):
    # await bot.send_message(chat_id, f"Вы выбрали сервер: {pve_server_name}")
    pve = get_server_by_name(pve_servers_config, pve_server_name)
    if not pve:
        logging.error(f'PVE server config not found')
        return None

    pve = ProxMox(proxmox_host=pve['host'], user=pve['user'], token_name=pve['token_name'], token_value=pve['token_value'])
    nodes = pve.get_node_vms()
    for node_name, vms in nodes.items():
        await bot.send_message(chat_id, f"{node_name}")
        
        for vm_id, vm_data in vms.items():
            vm_mem = int( vm_data['mem']/1024/1024/1024 )
            await bot.send_message(chat_id, f"{vm_id} **{vm_data['name']}** {vm_data['status']}\nCPU:{vm_data['cpus']} Mem: {vm_mem}G\nUptime: {vm_data['uptime']}")



# Регистрация роутеров
dp.include_router(router)

# Запуск бота
async def main():
    await dp.start_polling(bot)

# Загружаем список серверов из конфигурации
pve_servers_config = load_servers_config()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
