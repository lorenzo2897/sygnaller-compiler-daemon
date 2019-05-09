from queue import Queue
from threading import Thread, Event
from datetime import datetime
import pytz

import cache
import ssh
import verilog
import sftp
import tcl


class CompileError(Exception):
    pass


running_threads = {}
running_logs = {}


# ##########################################


def prepare_vivado_folder(project_id):
    if not cache.project_exists(project_id):
        q, k, d = ssh.start_exec_thread(f"rm -rf /home/ls2715/vivado_projects/p_{project_id}; "
                                        f"cp -r /home/ls2715/vivado_template /home/ls2715/vivado_projects/p_{project_id}")
        d.wait()
        if d.returncode > 0:
            raise CompileError("Could not copy the reference Vivado files to the project location")
        else:
            cache.write_cache(project_id, [])


def compile(project_id, verilog_sources, components, log, cancel_event):
    try:
        log.put("Build started at " + datetime.now(pytz.timezone('Europe/London')).strftime('%H:%M:%S'))

        log.put("Preparing Vivado project folder")
        prepare_vivado_folder(project_id)

        log.put("Determining which Verilog modules to compile")
        tcl_script = tcl.TclScript(f"/home/ls2715/vivado_projects/p_{project_id}/Pynq-Z1/base/base")

        for c in cache.cached_components(project_id):
            tcl_script.delete_IP(c)

        for component in components:
            axi_wrapper = verilog.create_wrapper(component, verilog_sources)
            cache.write_axi_wrapper(project_id, component.name, axi_wrapper)
            tcl_script.create_IP(component.name, component.register_count())
            tcl_script.edit_IP(component.name, f"/home/ls2715/vivado_projects/p_{project_id}/wrappers/{component.name}")
            tcl_script.add_IP(component.name)

        tcl_script.compile()

        log.put("Generating the automated build script for Vivado")
        cache.write_tcl_script(project_id, str(tcl_script))

        if len(components) > 0:
            log.put("Uploading the source code to Vivado servers")
            sftp.put_file(cache.get_wrappers_dir(project_id), f"/home/ls2715/vivado_projects/p_{project_id}")
        else:
            log.put("Skipping source code upload (no components to compile)")

        log.put("Uploading the build script to Vivado servers")
        sftp.put_file(cache.get_script_path(project_id), f"/home/ls2715/vivado_projects/p_{project_id}/script.tcl")

        if cancel_event.is_set():
            raise RuntimeError("Cancelled by user")

        log.put("Updating the local cache with the latest changes")
        cache.write_cache(project_id, [c.name for c in components])

        # run
        log.put("Starting Vivado build!")
        _, _, done = ssh.start_exec_thread(
            f"vivado -mode batch -source /home/ls2715/vivado_projects/p_{project_id}/script.tcl",
            out_queue=log,
            kill_event=cancel_event
        )

        done.wait()
        log.put(f"Build completed with return code {done.returncode}")

        if done.returncode == 2:
            raise CompileError("Synthesis failed")
        elif done.returncode == 3:
            raise CompileError("Hardware implementation failed")
        elif done.returncode > 0:
            raise CompileError("Build failed due to unknown error")

        if cancel_event.is_set():
            raise RuntimeError("Cancelled by user")

        # copy bit and tcl back to local server
        log.put("Downloading the generated files from Vivado servers")
        sftp.get_file(f"/home/ls2715/vivado_projects/p_{project_id}/overlay.tcl", cache.get_overlay_tcl_path(project_id))
        sftp.get_file(f"/home/ls2715/vivado_projects/p_{project_id}/overlay.bit", cache.get_overlay_bit_path(project_id))

        log.put("All done.")
    except CompileError as e:
        log.put(str(e.args[0]))
    except RuntimeError as e:
        log.put("Build failed: " + str(e.args[0]))
    except Exception as e:
        log.put("Build failed with a " + type(e).__name__)

    running_threads.pop(project_id, None)


def start_compilation(project_id, verilog_sources, components):
    # only one build per project at a time
    if project_id in running_threads:
        if not running_threads[project_id].is_alive():
            running_threads.pop(project_id)
        else:
            raise CompileError("A build is already running for this project")

    log_queue = Queue()
    cancel_event = Event()
    running_logs[project_id] = log_queue
    t = Thread(target=compile, args=(project_id, verilog_sources, components, log_queue, cancel_event), daemon=True)
    t.cancel = cancel_event
    running_threads[project_id] = t
    t.start()


def cancel_compilation(project_id):
    if project_id in running_threads:
        running_threads[project_id].cancel.set()
    else:
        raise CompileError("There is not build currently running for this project")
