
class PortSpec:
    def __init__(self, name: str, port_type: str):
        self.name = name
        self.port_type = port_type  # clock, input, output, scope, video in, video x, video y, video ready, video out


class ComponentSpec:
    def __init__(self, name, ports=None):
        self.name = name
        if ports is None:
            self.port_list = []
        else:
            self.port_list = [PortSpec(p["name"], p["type"]) for p in ports]  # PortSpec[]

    def register_count(self):
        return max(4, len(self.port_list) + 1)

    def has_scope_port(self):
        return 'scope' in [p.port_type for p in self.port_list]

    def has_video_out_port(self):
        return 'video out' in [p.port_type for p in self.port_list]

    def is_output(self, port_index):
        return len(self.port_list) > port_index and self.port_list[port_index].port_type == 'output'

    def output_ports(self):
        return ['module_output'+str(index+1) for index, port_spec in enumerate(self.port_list) if port_spec.port_type == 'output']

# register 0 is the scope
# register n corresponds to the (n-1)th port on the module


# *****************************************
# Unit tests
# *****************************************

import unittest


class TestComponent(unittest.TestCase):

    def test_init(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"},
            {"name": "p2", "type": "output"}
        ])
        self.assertEqual(c.name, "name")
        self.assertEqual(len(c.port_list), 2)
        self.assertEqual(c.port_list[0].name, "p1")
        self.assertEqual(c.port_list[1].port_type, "output")

    def test_count1(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"},
            {"name": "p2", "type": "output"}
        ])
        self.assertEqual(c.register_count(), 4)

    def test_count2(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"},
            {"name": "p2", "type": "output"},
            {"name": "p3", "type": "output"},
            {"name": "p4", "type": "output"}
        ])
        self.assertEqual(c.register_count(), 5)

    def test_scope_port(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"}
        ])
        self.assertFalse(c.has_scope_port())
        c = ComponentSpec("name", [
            {"name": "p1", "type": "scope"}
        ])
        self.assertTrue(c.has_scope_port())

    def test_video_port(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"}
        ])
        self.assertFalse(c.has_video_out_port())
        c = ComponentSpec("name", [
            {"name": "p1", "type": "video out"}
        ])
        self.assertTrue(c.has_video_out_port())

    def test_output(self):
        c = ComponentSpec("name", [
            {"name": "p1", "type": "input"},
            {"name": "p2", "type": "output"},
            {"name": "p3", "type": "scope"},
            {"name": "p4", "type": "output"}
        ])
        self.assertFalse(c.is_output(0))
        self.assertTrue(c.is_output(1))
        self.assertFalse(c.is_output(2))
        self.assertTrue(c.is_output(3))
        self.assertFalse(c.is_output(4))


if __name__ == '__main__':
    unittest.main()
