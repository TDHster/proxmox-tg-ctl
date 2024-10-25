#proxmox.py
from proxmoxer import ProxmoxAPI
import json


def load_servers_config(json_file='servers.json'):
    with open(json_file, 'r') as f:
        return json.load(f)
    
    
def get_server_by_name(servers, pve_node_name):
    for server in servers['servers']:
        if server['name'] == pve_node_name:
            return server
    return None  # Вернуть None, если сервер с таким именем не найден


class ProxMox():
    def __init__(self, proxmox_host, user, token_name, token_value, verify_ssl=False):
        self.proxmox_host = ProxmoxAPI(proxmox_host, user=user, token_name=token_name, token_value=token_value, verify_ssl=verify_ssl)
        self.nodes_resources = {}
    
    def get_node_vms(self):
        # Инициализируем словарь для хранения информации о нодах и виртуальных машинах
        node_vm_dict = {}

        try:
            nodes = self.proxmox_host.nodes.get()
        except Exception as e:
            print(e)
            return None
        
        print(f'\nHost: {self.proxmox_host}')

        for node in nodes:
            node_name = node['node']
            node_status = node['status']

            print(f"\n  Node: {node_name}, {node_status}.")
            
            # Получаем список виртуальных машин на данном узле
            try:
                vms = self.proxmox_host.nodes(node_name).qemu.get()
            except Exception as e:
                print(e)
                return None
            
            # Инициализируем словарь для хранения информации о VM для каждой ноды
            node_vm_dict[node_name] = {}

            if vms:
                for vm in vms:
                    # print(f'{vm=}')
                    vm_id = vm['vmid']
                    vm_name = vm.get('name', 'No Name')  # Имя может отсутствовать
                    vm_status = vm['status']
                    vm_cpus = vm['cpus']
                    vm_cpu_load = vm['cpu']
                    vm_maxmem = vm['maxmem']
                    vm_mem_usage = vm['mem']

                    # Получаем статус конкретной виртуальной машины для uptime
                    vm_status_info = self.proxmox_host.nodes(node_name).qemu(vm_id).status.current.get()
                    uptime_seconds = vm_status_info.get('uptime', 0)
                    uptime_string = self.convert_sec_to_human_readable(uptime_seconds)

                    # Добавляем информацию о VM в словарь
                    node_vm_dict[node_name][vm_id] = {
                        'name': vm_name,
                        'status': vm_status,
                        'cpus': vm_cpus,
                        'cpu_load': vm_cpu_load,
                        'mem': vm_maxmem,
                        'mem_usage': vm_mem_usage,
                        'uptime': uptime_string  
                    }

                    print(f"    VM ID: {vm_id}, {vm_status}, {vm_cpus} CPUs, {int(vm_maxmem/1024/1024/1024)}G, {vm_name}, Uptime: {uptime_string}")
            else:
                print("  No VMs found on this node. (Or access error)")

        # Возвращаем словарь с нодами и VMID, а также их параметрами
        return node_vm_dict
          
                
    def get_proxmox_logs_for_vm(self, node_name, vm_id):
        # Получаем список всех задач на узле
        tasks = self.proxmox_host.nodes(node_name).tasks.get()

        # Фильтруем задачи по ID виртуальной машины
        vm_tasks = [task for task in tasks if str(vm_id) in task['id']]

        # Выводим логи для каждой задачи
        for task in vm_tasks:
            task_id = task['upid']
            task_logs = self.proxmox_host.nodes(node_name).tasks(task_id).log.get()

            print(f"\nLogs for task {task_id} (VM ID: {vm_id}):")
            for log_entry in task_logs:
                print(log_entry['t'], log_entry['n'])  # t - время записи, n - сообщение лога


    def convert_sec_to_human_readable(self, uptime_seconds):
                    years = uptime_seconds // (365 * 24 * 3600)
                    months = (uptime_seconds % (365 * 24 * 3600)) // (30 * 24 * 3600)
                    days = (uptime_seconds % (30 * 24 * 3600)) // (24 * 3600)
                    hours = (uptime_seconds % (24 * 3600)) // 3600
                    minutes = (uptime_seconds % 3600) // 60

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
                    
                    return uptime_string
                

    def get_proxmox_logs_for_node(self, node_name):
        # Получаем список завершённых задач на узле
        tasks = self.proxmox_host.nodes(node_name).tasks.get()

        # Для каждой задачи получаем её лог
        for task in tasks:
            task_id = task['upid']  # Идентификатор задачи
            task_logs = self.proxmox_host.nodes(node_name).tasks(task_id).log.get()
            
            print(f"\nLogs for task {task_id}:")
            for log_entry in task_logs:
                print(log_entry['t'], log_entry['n'])  # t - время записи, n - сообщение лога


    def shutdown_vm(self, node_name, vm_id):
        print(f"    Restarting VM {vm_id} on {node_name}...")
        try:        
            self.proxmox_host.nodes(node_name).qemu(vm_id).status.shutdown.post()
        except Exception as e:
            print(e)
            return e
        return True
        
    def start_vm(self, node_name, vm_id):
        try:
            self.proxmox_host.nodes(node_name).qemu(vm_id).status.start.post()
        except Exception as e:
            print(e)
            return e
        return True

    def stop_vm(self, node_name, vm_id):
        try:
            self.proxmox_host.nodes(node_name).qemu(vm_id).status.stop.post()
        except Exception as e:
            print(e)
            return e
        return True

    def reboot_vm(self, node_name, vm_id):
        # self.proxmox_host.nodes(node_name).qemu(vm_id).status.restart.post()  # not implemented
        try:
            self.proxmox_host.nodes(node_name).qemu(vm_id).status.reboot.post()
        except Exception as e:
            print(e)
            return e
        return True


if __name__ == '__main__':
    servers = load_servers_config()

    server_names = [server['name'] for server in servers['servers']]
    print(f'{server_names=}')

    for server in servers['servers']:
        print(f"Host: {server['host']}, Token Name: {server['token_name']}")
        pve = ProxMox(proxmox_host=server['host'], user=server['user'], token_name=server['token_name'], token_value=server['token_value'])
        pve.get_node_vms()
    
    # pve = ProxMox(proxmox_host=proxmox_host, user=proxmox_user, token_name=token_name, token_value=token_value)
    # pve.get_node_vms()
    # pve.stop_vm('pve2', 226)
    
