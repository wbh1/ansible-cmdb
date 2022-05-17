from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.vars.hostvars import HostVars

from ansiblecmdb import Ansible


class AnsibleViaAPI(Ansible):
    """
    Gather Ansible host information using the Ansible Python API.

    `fact_dirs` is a list of paths to directories containing facts
    gathered by Ansible's 'setup' module.

    `inventory_paths` is a list with files or directories containing the
    inventory.
    """
    def load_inventories(self):
        """Load host inventories using the Ansible Python API."""
        loader = DataLoader()
        inventory = InventoryManager(loader=loader, sources=self.inventory_paths)
        variable_manager = VariableManager(loader=loader, inventory=inventory)
        hostvars = HostVars(inventory, variable_manager, loader)

        # Handle limits here because Ansible understands more complex
        # limit syntax than ansible-cmdb (e.g. globbing matches []?*
        # and :& and matches).  Remove any extra hosts that were
        # loaded by facts.  We could optimize a bit by arranging to
        # load facts after inventory and skipping loading any facts
        # files for hosts not included in limited hosts, but for now
        # we do the simplest thing that can work.
        if self.limit:
            inventory.subset(self.limit)
            limited_hosts = inventory.get_hosts()
            for h in self.hosts.keys():
                if h not in limited_hosts:
                    del self.hosts[h]

        for host in inventory.get_hosts():

            vars = hostvars[host.name]

            hostname = vars['inventory_hostname']
            self.update_hostvars(hostname, {
                'name': hostname,
                'groups': vars['group_names'],
                'hostvars': vars
            })

    def update_hostvars(self, hostname, key_values):
        """
        Update just the hostvars for a host, creating it if it did not exist
        from the fact collection stage.
        """
        default_empty_host = {
            'name': hostname,
            'groups': [],
            'hostvars': {}
        }
        host_info = self.hosts.get(hostname, default_empty_host)
        host_info.update(key_values)
        self.hosts[hostname] = host_info

    def get_hosts(self):
        """
        Return a dict of parsed hosts info, with the limit applied if required.
        """
        # We override this method since we already applied the limit
        # when we loaded the inventory.
        return self.hosts
