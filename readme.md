# Proxmox VM Control Bot

This project is a Telegram bot designed to simplify the management of virtual machines (VMs) on Proxmox servers. Using this bot, you can manage your virtual machines by retrieving their status and performing actions such as starting, stopping, and rebooting directly through Telegram.

## Key Features

- Retrieve a list of all Proxmox servers and the virtual machines on each server.
- Manage virtual machines: start, stop, reboot.
- Retrieve the status of each virtual machine, including resource usage (CPU, memory), and uptime information.
- Display Proxmox operation logs for each virtual machine.
- Quickly access Proxmox nodes using an inline keyboard in Telegram.

## Project Structure

### 1. `proxmox.py`

This module:
- Connects to Proxmox servers via API.
- Retrieves data on virtual machines, including their status, resource usage, and uptime.
- Performs actions on virtual machines (start, stop, reboot).
- Converts uptime data into a human-readable format.

### 2. `pve_control_bot.py`

A Telegram bot based on the `aiogram` library that:
- Provides users with an interface to manage Proxmox servers via chat.
- Handles commands and callbacks to retrieve information about VMs and manage them.
- Uses an inline keyboard for quick selection of servers and virtual machines.

## Getting Started

### 1. Install dependencies

Install the required libraries:

```bash
pip install -r requirements.txt
```
### 2. Create a token in PVE (e.g., through the web interface)

In the Datacenter section:
1. Create a user `startstop_vm_bot` in Datacenter/Permissions.
2. Create a role `start_stop_vm_bot` with the permissions: `VM.Monitor`, `VM.Audit`, `VM.PowerMgmt`, `Sys.PowerMgmt`, `Sys.Audit` in Datacenter/Permissions/Roles.
3. Create an API token for `start_stop_vm_bot` in Datacenter/Permissions/API Tokens.
4. Assign the role to both the user and the token in Datacenter/Permissions for /.

### 3. Server Configuration

Create a `servers.json` file where information about your Proxmox servers will be stored, for example:

(A sample file `servers_example.json` is provided. Copy it to `servers.json` and make necessary changes.)

```json
{
  "servers": [
    {
      "name": "Proxmox-1",
      "host": "proxmox1.example.com",
      "user": "root@pam",
      "token_name": "api-token",
      "token_value": "your-token-here"
    }
  ]
}
```
### 4. Environment Variables
Create a .env file and add your bot token and the Telegram IDs of authorized users (which can be obtained through @myidbot):

```env
BOT_TOKEN=your-telegram-bot-token
ALLOWED_USERS=111111,2222222
```
### 5. Run the Bot
Run the bot:

```python pve_control_bot.py```
Now the bot will be active and ready to manage your virtual machines.

### 6. Usage
Commands:
/start — Initializes the bot and displays a list of Proxmox servers. You can also press the inline button "List PVE Servers" to view the servers.
VM Management:
After selecting a server, you will see a list of virtual machines on it, along with buttons to manage each VM (start, stop, reboot).

Example of Bot Usage:
You enter the command /start.
Select a server from the list.
Get a list of all VMs on the server with their statuses and metrics.
Select a VM to manage and perform actions via inline buttons.
Warning:
The commands for rebooting, stopping, and starting a VM will be immediately sent to the server without additional warnings.




# Russian language

# Proxmox VM Control Bot

Этот проект представляет собой Telegram-бот, который упрощает управление виртуальными машинами на серверах Proxmox. Используя этот бот, вы можете управлять своими виртуальными машинами (VM), получая информацию о статусе VM, а также выполняя такие действия, как запуск, остановка и перезагрузка прямо через Telegram.

## Основные возможности

- Получение списка всех серверов Proxmox и виртуальных машин, находящихся на каждом сервере.
- Управление виртуальными машинами: запуск, остановка, перезагрузка.
- Получение статуса каждой виртуальной машины, включая использование ресурсов (CPU, память), и информацию о времени работы (uptime).
- Вывод логов операций Proxmox для каждой виртуальной машины.
- Быстрый доступ к узлам Proxmox с помощью Inline-клавиатуры в Telegram.

## Структура проекта

### 1. `proxmox.py`

Модуль, который:
- Подключается к Proxmox серверам через API.
- Получает данные о виртуальных машинах, включая их статус, использование ресурсов и uptime.
- Осуществляет действия с виртуальными машинами (запуск, остановка, перезагрузка).
- Преобразует данные uptime в человекочитаемый формат.

### 2. `pve_control_bot.py`

Telegram-бот на базе библиотеки `aiogram`, который:
- Предоставляет пользователям интерфейс для управления Proxmox серверами через чат.
- Обрабатывает команды и колбэки для получения информации о VM и управления ими.
- Использует inline-клавиатуру для быстрого выбора серверов и виртуальных машин.

## Как начать работу

### 1. Установка зависимостей

Установите необходимые библиотеки:

pip install -r requirements.txt

### 2. Создайте токен в pve, например через web интерфейс.
В разделе Datacenter
1. Создайте пользователя startstop_vm_bot в Datacenter/Permissions user
2. Создайте роль start_stop_vm_bot с правами: VM.Monitor, VM.Audit, VM.PowerMgmt, Sys.PowerMgmt, Sys.Audit в Datacenter/Permissions/Roles
3. Создайте токен start_stop_vm_bot  в Datacenter/Permissions/API Tokens
4. Добавьте права и пользователю и токену назначив созданную role в Datacenter/Permissions для /

### 3. Настройка конфигурации серверов
Создайте файл servers.json, где будет храниться информация о ваших серверах Proxmox, например:

(Есть файл пример servers_example.json, скопируйте его в servers.json и внесите изменения))
```json
{
  "servers": [
    {
      "name": "Proxmox-1",
      "host": "proxmox1.example.com",
      "user": "root@pam",
      "token_name": "api-token",
      "token_value": "your-token-here"
    }
  ]
}
```
### 4. Переменные окружения
Создайте файл .env и добавьте в него ваш токен бота и telegram id разрешенных пользователей (можно получить через @myidbot):

BOT_TOKEN=your-telegram-bot-token
ALLOWED_USERS=111111,2222222

### 5. Запуск
Запустите бота:

python pve_control_bot.py

Теперь бот будет работать и управлять вашими виртуальными машинами.

### 6. Использование
Команды

/start — Инициализирует бота, отображает список серверов Proxmox.
или нажмите на клавиатуре "Список PVE серверов" 

Управление VM — После выбора сервера, вы увидите список виртуальных машин на нём, а также кнопки для управления каждой VM (старт, остановка, перезагрузка).

#### Пример работы
Вы вводите команду /start.
Выбираете сервер из списка.
Получаете список всех VM на сервере с их статусами и метриками.
Выбираете VM для управления и выполняете действия через Inline-кнопки.

### Осторожно
Команды перезагрузка, остановка, запуск будут сразу отправленны на сервер, без дополнительных предупреждений.



