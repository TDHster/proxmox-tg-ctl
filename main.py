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
# Выводим информацию о каждом узле и его виртуальных машинах
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
            print(f"    VM ID: {vm_id}, {vm_status}, {vm_name} ")
            
            # vm_id_for_reboot = 226
            # if vm_id == vm_id_for_reboot:
            #     print(f"\n    Restarting VM {vm_id_for_reboot}...")
            #     proxmox.nodes(node_name).qemu(vm_id).status.reboot.post()
            #     print(f"    VM {vm_id_for_reboot} has been restarted.")

    else:
        print("  No VMs found on this node.")
        
        
node_name = "pve2"  # Имя вашего узла
vm_id = 226  # ID виртуальной машины

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
        
  
#-------------
      
# # Получаем список всех задач, выполненных на узле
# tasks = proxmox.nodes(node_name).tasks.get()

# # Выводим задачи и логи каждой задачи
# for task in tasks:
#     task_id = task['upid']
#     task_type = task['type']
#     task_status = task['status']
#     task_start_time = task['starttime']

#     print(f"\nTask ID: {task_id}, Type: {task_type}, Status: {task_status}, Start Time: {task_start_time}")
    
#     # Получаем логи задачи
#     task_logs = proxmox.nodes(node_name).tasks(task_id).log.get()
#     for log_entry in task_logs:
#         print(log_entry['t'], log_entry['n'])  # t - время записи, n - сообщение лога

