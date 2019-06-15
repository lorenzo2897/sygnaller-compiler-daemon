import subprocess
from queue import Queue
from threading import Thread, Event


def remote_exec(command, output_queue: Queue, kill_event: Event, done_event: Event, intercept_progress):
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
                if intercept_progress:
                    intercept_log(line, output_queue)
        except:
            p.kill()
            p.wait()

    done_event.returncode = p.returncode
    done_event.set()


def start_exec_thread(command, out_queue=None, kill_event=None, intercept_progress=False):
    if out_queue is None:
        out_queue = Queue()

    if kill_event is None:
        kill_event = Event()

    done_event = Event()

    t = Thread(target=remote_exec, args=(command, out_queue, kill_event, done_event, intercept_progress), daemon=True)
    t.start()

    return out_queue, kill_event, done_event


def intercept_log(line, log_queue):
    if line.startswith('Launching synthesis step'):
        log_queue.progress = 20

    elif 'Launched synth_1...' in line:
        log_queue.progress = 30

    elif line.startswith('Synthesis complete'):
        log_queue.progress = 40

    elif line.startswith('Starting Logic Optimization Task'):
        log_queue.progress = 50

    elif line.startswith('Starting Placer Task') or line.startswith('Starting Incremental Placer Task'):
        log_queue.progress = 60

    elif line.startswith('Starting Routing Task') or line.startswith('Starting Incremental Route Task'):
        log_queue.progress = 70

    elif line.startswith('Routing Is Done.'):
        log_queue.progress = 80

    elif line.startswith('Implementation complete'):
        log_queue.progress = 90
    pass


# *****************************************
# Unit tests
# *****************************************

import unittest


class TestSsh(unittest.TestCase):

    def test_intercept_log(self):
        q = Queue()
        q.progress = 0
        intercept_log("[time] Launched synth_1...", q)
        self.assertEqual(q.progress, 30)
        intercept_log("Synthesis complete (time)", q)
        self.assertEqual(q.progress, 40)

    def test_remote_exec(self):
        command = 'echo hello'
        out_queue = Queue()
        kill_event = Event()
        done_event = Event()
        remote_exec(command, out_queue, kill_event, done_event, False)
        self.assertTrue(done_event.is_set())
        self.assertFalse(out_queue.empty())
        o = ""
        while o != "hello\n":
            o = out_queue.get_nowait()
        self.assertEqual(done_event.returncode, 0)

    def test_remote_error(self):
        command = 'false'
        out_queue = Queue()
        kill_event = Event()
        done_event = Event()
        remote_exec(command, out_queue, kill_event, done_event, False)
        self.assertTrue(done_event.is_set())
        self.assertEqual(done_event.returncode, 1)


if __name__ == '__main__':
    unittest.main()
