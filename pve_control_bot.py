#pve_control_bot.py
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
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


load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
allowed_users_str = os.getenv('ALLOWED_USERS')  # String like "11111111,22222222"
if allowed_users_str:
    ALLOWED_USERS = [int(user_id) for user_id in allowed_users_str.split(',')]
else:
    ALLOWED_USERS = []
    raise ValueError('ALLOWED_USERS of this bot is empty')

logging.basicConfig(level=logging.INFO)

# Создаем объекты для работы с ботом
bot = Bot(token=API_TOKEN, session=AiohttpSession(), default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage())
router = Router()


async def get_pves_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    # Создаем кнопки для каждого сервера
    for server in pve_servers_config['servers']:
        # logging.info(f"Создание кнопки для сервера: {server['name']}, callback_data='pve_{server['name']}'")
        keyboard.button(text=server['name'], callback_data=f"pve_{server['name']}")  # Генерируем уникальный callback_data для каждого сервера
    
    return keyboard.as_markup()


# Обработчик команды /start с проверкой ID пользователя
@router.message(F.text == "Список PVE серверов")
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    if message.from_user.id in ALLOWED_USERS:
        kb = [
            [types.KeyboardButton(text="Список PVE серверов")]        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("VM PVE control", reply_markup=keyboard)        
        await message.answer("Выберите сервер:", reply_markup=await get_pves_inline_keyboard())
    else:
        await message.answer("У вас нет доступа к этому боту.")


@router.callback_query(F.data.startswith("pve_"))  
async def process_pveserver_callback(callback_query: types.CallbackQuery):
    # logging.info(f"Получен callback_data: {callback_query.data}")  # Логируем данные колбэка

    if callback_query.from_user.id not in ALLOWED_USERS:
        await callback_query.answer("У вас нет доступа к этой команде!", show_alert=True)
        return

    # Извлекаем название сервера из callback_data
    server_name = callback_query.data[4:]  # Убираем префикс "pve_"

    # Получаем ID чата из callback_query.message и отправляем сообщение явно через bot.send_message
    chat_id = callback_query.message.chat.id
    await bot.send_message(chat_id, f"Получаю список vm с сервера: <b>{server_name}</b>")
    await callback_query.answer()  # Это закрывает уведомление о колбэке
    await pveserver_selected(server_name, chat_id=chat_id)


async def get_vmid_control_inline_keyboard(pve_host, vm_id) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=f"▶️ Start", callback_data=f"vmid_{vm_id}_{pve_host}_start")
    keyboard.button(text=f"⏹️ Stop", callback_data=f"vmid_{vm_id}_{pve_host}_stop")
    keyboard.button(text=f"🔃 Reboot", callback_data=f"vmid_{vm_id}_{pve_host}_reboot")
    
    return keyboard.as_markup()


async def pveserver_selected(pve_server_name, chat_id):
    # await bot.send_message(chat_id, f"PVE сервер: {pve_server_name}")
    pve_server_config = get_server_by_name(pve_servers_config, pve_server_name)
    if not pve_server_config:
        logging.error(f'PVE server config not found')
        return None

    pve = ProxMox(proxmox_host=pve_server_config['host'], user=pve_server_config['user'], token_name=pve_server_config['token_name'], token_value=pve_server_config['token_value'])
    nodes = pve.get_node_vms()
    if not nodes:
        await bot.send_message(chat_id, f"Error. Something bad in bot happens.")
        return None
    for node_name, vms in nodes.items():
        await bot.send_message(chat_id, f"Node: <u><b>{node_name}</b></u>")
        for vm_id, vm_data in vms.items():
            vm_memory = int( vm_data['mem']/1024/1024/1024 )
            # vm_status = vm_data['status'] 
            match vm_data['status']:
                case 'stopped':
                    vm_status = vm_data['status'] + ' 🔴'
                case 'running':
                    vm_status = vm_data['status'] + ' 🟢'
                case _:
                    vm_status = vm_data['status'] + ' 🟡'
            uptime = f"\nUptime: {vm_data['uptime']}" if vm_data['uptime'] else ''
            await bot.send_message(chat_id, 
                                   (f"VMID: {vm_id}, <b>{vm_data['name']}</b>, {vm_status}\n"
                                    f"CPU: {vm_data['cpus']}, {vm_data['cpu_load']*100:.1f}% Mem: {vm_memory}G"
                                    f"{uptime}"),
                                    reply_markup=await get_vmid_control_inline_keyboard(pve_server_config['name'], vm_id))


# Обработчик колбэков, начинающихся на "vmid_"
@router.callback_query(F.data.startswith("vmid_"))
async def process_vmid_callback(callback_query: types.CallbackQuery):
    # Получаем callback_data
    callback_data = callback_query.data

    # Разбираем callback_data: формат "vmid_{vm_id}_{pve_host}_{action}"
    callback_parts = callback_data.split("_")

    if len(callback_parts) < 4:
        await callback_query.answer("Неверный формат команды", show_alert=True)
        return

    vm_id = callback_parts[1]       # Извлекаем vm_id
    pve_node_name = callback_parts[2]     # Извлекаем pve_host
    action = callback_parts[3]       # Извлекаем action (start/stop/reboot)

    chat_id = callback_query.message.chat.id
    await bot.send_message(chat_id, f"VM {vm_id} на {pve_node_name} отправка команды: {action}")

    # Логируем или выводим информацию
    # await callback_query.answer(f"Выбрана VM: {vm_id} на хосте {pve_node_name} для действия: {action}")

    # Здесь можно добавить логику для выполнения действия с VM, например:
    # if action == "start":
    #     await start_vm(pve_host, vm_id)
    # elif action == "stop":
    #     await stop_vm(pve_host, vm_id)
    # elif action == "reboot":
    #     await reboot_vm(pve_host, vm_id)
    pve_server_config = get_server_by_name(pve_servers_config, pve_node_name)
    if not pve_server_config:
        logging.error(f'PVE server config not found')
        return None

    match action:
        case 'start':
            pve = ProxMox(proxmox_host=pve_server_config['host'], user=pve_server_config['user'], token_name=pve_server_config['token_name'], token_value=pve_server_config['token_value'])
            # pve.get_node_vms()
            result = pve.start_vm(pve_node_name, vm_id=vm_id)
            await callback_query.answer(f"Команда в {pve_node_name} отправлена")
            if result != True:
                await bot.send_message(chat_id, f"Ошибка: {result}")  
        case 'stop':
            pve = ProxMox(proxmox_host=pve_server_config['host'], user=pve_server_config['user'], token_name=pve_server_config['token_name'], token_value=pve_server_config['token_value'])
            result = pve.stop_vm(pve_node_name, vm_id=vm_id)
            await callback_query.answer(f"Команда в {pve_node_name} отправлена")
            if result != True:
                await bot.send_message(chat_id, f"Ошибка: {result}")  
        case 'reboot':
            pve = ProxMox(proxmox_host=pve_server_config['host'], user=pve_server_config['user'], token_name=pve_server_config['token_name'], token_value=pve_server_config['token_value'])
            result = pve.reboot_vm(pve_node_name, vm_id=vm_id)
            await callback_query.answer(f"Команда в {pve_node_name} отправлена")
            if result != True:
                await bot.send_message(chat_id, f"Ошибка: {result}")    
        case _:
            await callback_query.answer(f"Неизвестная команда, ничего не отправлено.")


    await callback_query.answer(f"Выполняю {action} на VM {vm_id} в {pve_node_name}.")


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
