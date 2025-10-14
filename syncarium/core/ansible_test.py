import sys
import syncarium.options.global_vars as global_vars

sys.path.insert(0, global_vars.ANSIBLE_API_PATH)

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C

# Configuración básica
loader = DataLoader()
inventory = InventoryManager(loader=loader, sources='inventario.ini')
variable_manager = VariableManager(loader=loader, inventory=inventory)

# Contexto de ejecución
context.CLIARGS = {
    'connection': 'ssh',
    'module_path': None,
    'forks': 10,
    'become': None,
    'become_method': None,
    'become_user': None,
    'check': False,
    'diff': False,
    'verbosity': 0
}

# Callback personalizado
class ResultCallback(CallbackBase):
    def v2_runner_on_ok(self, result, **kwargs):
        print(f"RESULTADO: {result._result}")

# Crear la tarea
play_source = {
    'name': "Ping remoto",
    'hosts': 'raspberrypi',
    'gather_facts': 'no',
    'tasks': [
        {'action': {'module': 'ping'}}
    ]
}

play = Play().load(play_source, loader=loader, variable_manager=variable_manager)

# Ejecutar
callback = ResultCallback()
tqm = None
try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords={},
        stdout_callback=callback,
    )
    tqm.run(play)
finally:
    if tqm:
        tqm.cleanup()
