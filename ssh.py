import subprocess
from queue import Queue
from threading import Thread, Event


def remote_exec(command, output_queue: Queue, kill_event: Event, done_event: Event):
    p = subprocess.Popen([
        'ssh',
        '-o',
        'ProxyCommand=ssh -W %h:%p ls2715@shell3.doc.ic.ac.uk',
        '-o',
        'StrictHostKeyChecking no',
        'ls2715@ee-mill2.ee.ic.ac.uk',
        command
    ], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, bufsize=0, universal_newlines=True)

    while p.poll() is None:
        if kill_event.is_set():
            p.kill()
            p.wait()
            break

        try:
            line = p.stdout.readline()
            if line is not None and line != '':
                output_queue.put(line)
        except:
            p.kill()
            p.wait()

    done_event.returncode = p.returncode
    done_event.set()


def start_exec_thread(command, out_queue=None, kill_event=None):
    if out_queue is None:
        out_queue = Queue()

    if kill_event is None:
        kill_event = Event()

    done_event = Event()

    t = Thread(target=remote_exec, args=(command, out_queue, kill_event, done_event), daemon=True)
    t.start()

    return out_queue, kill_event, done_event
