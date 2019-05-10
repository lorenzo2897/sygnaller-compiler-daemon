
class ComponentSpec:
    def __init__(self, name, ports=None):
        self.name = name
        if ports is None:
            self.port_list = []
        else:
            self.port_list = ports  # clock, input, output, scope

    def register_count(self):
        return max(4, len(self.port_list) + 1)

    def has_scope_port(self):
        return 'scope' in self.port_list

    def is_output(self, port_index):
        return len(self.port_list) > port_index and self.port_list[port_index] == 'output'

    def output_ports(self):
        return ['module_output'+str(index+1) for index, port_type in enumerate(self.port_list) if port_type == 'output']

# register 0 is the scope
# register n corresponds to the (n-1)th port on the module
