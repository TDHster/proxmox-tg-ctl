from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем значения переменных
proxmox_host = os.getenv('PROXMOX_HOST')
proxmox_user = os.getenv('PROXMOX_USER')
token_name = os.getenv('PROXMOX_TOKEN_NAME')
token_value = os.getenv('PROXMOX_TOKEN_VALUE')

# Подключаемся к Proxmox API с использованием токена
proxmox = ProxmoxAPI(proxmox_host, user=proxmox_user, token_name=token_name, token_value=token_value, verify_ssl=False)

# Получаем список всех узлов (nodes)
nodes = proxmox.nodes.get()

print(f'\nHost: {proxmox_host}')

for node in nodes:
    node_name = node['node']
    node_status = node['status']

    print(f"\n  Node: {node_name}, {node_status}")
    
    # Получаем список виртуальных машин на данном узле
    vms = proxmox.nodes(node_name).qemu.get()

    if vms:
        # Выводим информацию о каждой виртуальной машине
        for vm in vms:
            vm_id = vm['vmid']
            vm_name = vm.get('name', 'No Name')  # Имя может отсутствовать
            vm_status = vm['status']

            # Получаем статус конкретной виртуальной машины
            vm_status_info = proxmox.nodes(node_name).qemu(vm_id).status.current.get()

            # Извлекаем аптайм
            uptime_seconds = vm_status_info.get('uptime', 0)

            # Переводим секунды в годы, месяцы, дни, часы, минуты
            years = uptime_seconds // (365 * 24 * 3600)
            months = (uptime_seconds % (365 * 24 * 3600)) // (30 * 24 * 3600)
            days = (uptime_seconds % (30 * 24 * 3600)) // (24 * 3600)
            hours = (uptime_seconds % (24 * 3600)) // 3600
            minutes = (uptime_seconds % 3600) // 60

            # Формируем строку аптайма
            uptime_str = []
            if years > 0:
                uptime_str.append(f"{years} years")
            if months > 0:
                uptime_str.append(f"{months} months")
            if days > 0:
                uptime_str.append(f"{days} days")
            if hours > 0:
                uptime_str.append(f"{hours} hours")
            if minutes > 0:
                uptime_str.append(f"{minutes} minutes")
                
            uptime_string = ', '.join(uptime_str)

            print(f"    VM ID: {vm_id}, {vm_status}, {vm_name} ", end='')
            print(f", Uptime: {uptime_string}") if uptime_string else None
            
    else:
        print("  No VMs found on this node.")

        
#-------------
    
# # Получаем список завершённых задач на узле
# tasks = proxmox.nodes(node_name).tasks.get()

# # Для каждой задачи получаем её лог
# for task in tasks:
#     task_id = task['upid']  # Идентификатор задачи
#     task_logs = proxmox.nodes(node_name).tasks(task_id).log.get()
    
#     print(f"\nLogs for task {task_id}:")
#     for log_entry in task_logs:
#         print(log_entry['t'], log_entry['n'])  # t - время записи, n - сообщение лога

#-------------


def get_proxmox_logs_for(node_name, vm_id):
    # Получаем список всех задач на узле
    tasks = proxmox.nodes(node_name).tasks.get()

    # Фильтруем задачи по ID виртуальной машины
    vm_tasks = [task for task in tasks if str(vm_id) in task['id']]

    # Выводим логи для каждой задачи
    for task in vm_tasks:
        task_id = task['upid']
        task_logs = proxmox.nodes(node_name).tasks(task_id).log.get()

        print(f"\nLogs for task {task_id} (VM ID: {vm_id}):")
        for log_entry in task_logs:
            print(log_entry['t'], log_entry['n'])  # t - время записи, n - сообщение лога


