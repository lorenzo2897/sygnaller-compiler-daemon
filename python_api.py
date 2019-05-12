import json


def template(args):
    return"""
import sys

print("Loading hardware components...", file=sys.stderr)

from pynq.overlays.base import BaseOverlay
import base64


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


class hw:
    __overlay = BaseOverlay('../overlay.bit')
    PMODA = __overlay.PMODA
    PMODB = __overlay.PMODB
    ARDUINO = __overlay.ARDUINO
    audio = __overlay.audio
    buttons = __overlay.buttons
    leds = __overlay.leds
    rgbleds = __overlay.rgbleds
    switches = __overlay.switches
    video = __overlay.video
{component_list}


class terminal:
    def imageFromDataURI(uri):
        print("~"+uri)
        
    def imageFromFile(filename):
        with open(filename, "rb") as f:
            print("~data:image;base64,"+ base64.b64encode(f.read()).decode('utf-8'))

    def showFigure(plt):
        import io
        buf = io.BytesIO()
        plt.gcf().savefig(buf, format='png')
        buf.seek(0)
        print("~data:image;base64,"+ base64.b64encode(buf.read()).decode('utf-8'))

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
        component_list.append(f"    {c.name} = Component(__overlay.{c.name}_0, {json.dumps(inputs)}, {json.dumps(outputs)})")

    return template({"component_list": '\n'.join(component_list)})


def write_python_api_to_file(components, filepath):
    with open(filepath, 'w') as f:
        f.write(make_python_api(components))
