import json


def template(args):
    return"""
import sys

print("Loading hardware components...", file=sys.stderr)

from pynq.overlays.base import BaseOverlay


class Component:
    def __init__(self, ip, inputs, outputs):
        self.__ip = ip
        self.__inputs = inputs
        self.__outputs = outputs
    
    def __setattr__(self, name, value):
        if name.startswith('_Component'):
            super().__setattr__(name, value)
        elif name in self.__inputs:
            self.__ip.write(self.__inputs[name], value)
        else:
            super().__setattr__(name, value)
        
    def __getattr__(self, name):
        if name in self.__outputs:
            return self.__ip.read(self.__outputs[name])
        else:
            raise AttributeError


_overlay = BaseOverlay('../overlay.bit')
PMODA = _overlay.PMODA
PMODB = _overlay.PMODB
ARDUINO = _overlay.ARDUINO
audio = _overlay.audio
buttons = _overlay.buttons
leds = _overlay.leds
rgbleds = _overlay.rgbleds
switches = _overlay.switches
video = _overlay.video
{component_list}

    """.format(**args)


def make_python_api(components):
    component_list = []

    for c in components:
        inputs = {}
        outputs = {}
        for i, p in enumerate(c.port_list):
            if p.port_type == 'input':
                inputs[p.name] = (i+1) * 4
            elif p.port_type == 'output':
                outputs[p.name] = (i+1) * 4
        component_list.append(f"{c.name} = Component(_overlay.{c.name}_0, {json.dumps(inputs)}, {json.dumps(outputs)})")

    return template({"component_list": '\n'.join(component_list)})


def write_python_api_to_file(components, filepath):
    with open(filepath, 'w') as f:
        f.write(make_python_api(components))
