from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Получаем значения переменных
proxmox_host = os.getenv('PROXMOX_HOST')
proxmox_user = os.getenv('PROXMOX_USER')
token_name = os.getenv('PROXMOX_TOKEN_NAME')
token_value = os.getenv('PROXMOX_TOKEN_VALUE')


def load_servers_config(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)
    

class ProxMox():
    def __init__(self, proxmox_host, user=proxmox_user, token_name=token_name, token_value=token_value, verify_ssl=False):
        self.proxmox_host = ProxmoxAPI(proxmox_host, user=user, token_name=token_name, token_value=token_value, verify_ssl=verify_ssl)
        self.nodes_resources = {}
    
    def get_node_vms(self):
        nodes = self.proxmox_host.nodes.get()
        print(f'\nHost: {proxmox_host}')

        for node in nodes:
            node_using_cpus = 0
            node_using_memory = 0
            node_name = node['node']
            node_status = node['status']
            node_maxcpu = node['maxcpu']
            node_maxmem = node['maxmem']

            print(f"\n  Node: {node_name}, {node_status}.")
            
            # Получаем список виртуальных машин на данном узле
            vms = self.proxmox_host.nodes(node_name).qemu.get()

            if vms:
                # Выводим информацию о каждой виртуальной машине
                for vm in vms:
                    # print(f'{vm=}')
                    # vm={'netout': 834110600874, 'status': 'running', 
                    # 'netin': 919137504232, 'maxdisk': 34359738368, 'disk': 0, 
                    # 'name': 'pbs-3', 'mem': 32 781 169 053, 'diskwrite': 0, 
                    # 'cpu': 0.0165168790855515, 'vmid': 312, 'diskread': 0, 
                    # 'uptime': 2550599, 'pid': 1680, 'cpus': 4, 'maxmem': 34 359 738 368}
                    vm_id = vm['vmid']
                    vm_name = vm.get('name', 'No Name')  # Имя может отсутствовать
                    vm_status = vm['status']
                    vm_cpus = vm['cpus']
                    vm_mem = vm['mem']

                    node_using_cpus += vm_cpus
                    node_using_memory += vm_mem

                    # Получаем статус конкретной виртуальной машины
                    vm_status_info = self.proxmox_host.nodes(node_name).qemu(vm_id).status.current.get()
                    uptime_seconds = vm_status_info.get('uptime', 0)
                    uptime_string = self.convert_sec_to_human_readable(uptime_seconds)

                    print(f"    VM ID: {vm_id}, {vm_status}, {vm_cpus} CPUs, {int(vm_mem/1024/1024/1024)}G, {vm_name} ", end='')
                    print(f", Uptime: {uptime_string}") if uptime_string else print()
                    
                print(f'  Free CPUs on {node_name}: {node_maxcpu-node_using_cpus} of {node_maxcpu} total.')
                print(f'  Free memory on {node_name}: {int((node_maxmem-node_using_memory)/1024/1024/1024)}G of {int(node_maxmem/1024/1024/1024)}G total')
                self.nodes_resources[node_name] = {}
                self.nodes_resources[node_name]['maxCPU'] = node_maxcpu
                self.nodes_resources[node_name]['maxmem'] = node_maxmem
                self.nodes_resources[node_name]['usingCPU'] = node_using_cpus
                self.nodes_resources[node_name]['usingmem'] = node_using_memory
                # print(self.nodes_resources)
            else:
                print("  No VMs found on this node.")
           
                
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
        self.proxmox_host.nodes(node_name).qemu(vm_id).status.shutdown.post()
        
    def start_vm(self, node_name, vm_id):
        self.proxmox_host.nodes(node_name).qemu(vm_id).status.start.post()

    def stop_vm(self, node_name, vm_id):
        self.proxmox_host.nodes(node_name).qemu(vm_id).status.stop.post()

    def reboot_vm(self, node_name, vm_id):
        # self.proxmox_host.nodes(node_name).qemu(vm_id).status.restart.post()  # not implemented
        self.proxmox_host.nodes(node_name).qemu(vm_id).status.reboot.post()


if __name__ == '__main__':
    servers = load_servers_config('servers.json')

    server_names = [server['name'] for server in servers['servers']]
    print(f'{server_names=}')

    for server in servers['servers']:
        print(f"Host: {server['host']}, Token Name: {server['token_name']}")
        pve = ProxMox(proxmox_host=server['host'], user=server['user'], token_name=server['token_name'], token_value=server['token_value'])
        pve.get_node_vms()
    
    # pve = ProxMox(proxmox_host=proxmox_host, user=proxmox_user, token_name=token_name, token_value=token_value)
    # pve.get_node_vms()
    # pve.stop_vm('pve2', 226)
    
