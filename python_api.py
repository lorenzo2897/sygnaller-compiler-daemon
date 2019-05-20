import json


def template(args):
    return"""
import sys
from contextlib import contextmanager

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


@contextmanager
def video_start():
    from pynq.lib.video import PIXEL_RGBA
    
    hdmi_in = video.hdmi_in
    hdmi_out = video.hdmi_out
    
    hdmi_in.configure(PIXEL_RGBA)
    hdmi_out.configure(hdmi_in.mode, PIXEL_RGBA)
    
    with hdmi_in.start(), hdmi_out.start():
        yield


ip = _overlay.sygnaller_dma_0


def process_frame(in_frame=None, out_frame=None, latency=0):
    if in_frame is None:
        in_frame = video.hdmi_in.readframe()
        
    if out_frame is None:
        out_frame = video.hdmi_out.newframe()
        
    ip.write(0x10, in_frame.physical_address)
    ip.write(0x18, out_frame.physical_address)
    ip.write(0x20, 1280)
    ip.write(0x28, 720)
    ip.write(0x30, latency)
    ip.write(0x00, 0x01)  # ap_start
    while (ip.read(0) & 0x4) == 0:  # ap_ready
        pass
    video.hdmi_out.writeframe(out_frame)


video.start = video_start
video.process_frame = process_frame

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
