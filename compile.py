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
        log.put("Build started at " + datetime.now(pytz.timezone('Europe/London')).strftime('%H:%M:%S') + "\n")

        log.progress = 2
        log.put("Preparing Vivado project folder\n")
        prepare_vivado_folder(project_id)

        log.put("Determining which Verilog modules to compile\n")
        tcl_script = tcl.TclScript(f"/home/ls2715/vivado_projects/p_{project_id}/Pynq-Z1/base/base")

        mappings = []
        line_number = 4
        for filename, source in verilog_sources.items():
            lines = len(source.splitlines())
            mappings.append({
                "file": filename,
                "start": line_number,
                "end": line_number + lines
            })
            line_number += lines + 1
        cache.put_source_mapping(project_id, mappings)

        for c in cache.cached_components(project_id):
            tcl_script.delete_IP(c)

        cache.clear_axi_wrappers(project_id)

        for component in components:
            axi_wrapper = verilog.create_wrapper(component, verilog_sources.values())
            cache.write_axi_wrapper(project_id, component.name, axi_wrapper)
            tcl_script.create_IP(component.name, component.register_count())
            tcl_script.edit_IP(component.name, f"/home/ls2715/vivado_projects/p_{project_id}/wrappers/{component.name}")
            tcl_script.add_IP(component.name)

        tcl_script.compile()

        log.progress = 5
        log.put("Generating the automated build script for Vivado\n")
        cache.write_tcl_script(project_id, str(tcl_script))

        if len(components) > 0:
            log.put("Uploading the source code to Vivado servers\n")
            sftp.put_file(cache.get_wrappers_dir(project_id), f"/home/ls2715/vivado_projects/p_{project_id}")
        else:
            log.put("Skipping source code upload (no components to compile)\n")

        log.progress = 10
        log.put("Uploading the build script to Vivado servers\n")
        sftp.put_file(cache.get_script_path(project_id), f"/home/ls2715/vivado_projects/p_{project_id}/script.tcl")

        if cancel_event.is_set():
            with open(cache.get_report_path(project_id), 'w') as f:
                f.write("ERROR\nBuild cancelled by user")
            raise RuntimeError("Cancelled by user")

        log.progress = 15
        log.put("Updating the local cache with the latest changes\n")
        cache.write_cache(project_id, [c.name for c in components])

        # run
        log.put("\nStarting Vivado build!\n")
        _, _, done = ssh.start_exec_thread(
            f"vivado -mode batch -nojournal -nolog -notrace -source /home/ls2715/vivado_projects/p_{project_id}/script.tcl",
            out_queue=log,
            kill_event=cancel_event,
            intercept_progress=True
        )

        done.wait()
        log.put(f"Build completed with return code {done.returncode}\n")
        log.progress = 95
        log.put("Downloading the build report from Vivado servers\n")
        sftp.get_file(f"/home/ls2715/vivado_projects/p_{project_id}/build_report.txt", cache.get_report_path(project_id))

        if done.returncode == 2:
            raise CompileError("Synthesis failed")
        elif done.returncode == 3:
            raise CompileError("Hardware implementation failed")
        elif done.returncode > 0:
            raise CompileError("Build failed due to unknown error")

        if cancel_event.is_set():
            with open(cache.get_report_path(project_id), 'w') as f:
                f.write("ERROR\nBuild cancelled by user")
            raise RuntimeError("Cancelled by user")

        # copy bit and tcl back to local server
        log.put("Downloading the generated files from Vivado servers\n")
        sftp.get_file(f"/home/ls2715/vivado_projects/p_{project_id}/overlay.tcl", cache.get_overlay_tcl_path(project_id))
        sftp.get_file(f"/home/ls2715/vivado_projects/p_{project_id}/overlay.bit", cache.get_overlay_bit_path(project_id))

        log.put("All done.\n")
    except CompileError as e:
        log.put(str(e.args[0]) + "\n")
    except RuntimeError as e:
        log.put("Build failed: " + str(e.args[0]) + "\n")
    except Exception as e:
        log.put("Build failed with a " + type(e).__name__ + "\n")

    log.progress = 100
    running_threads.pop(project_id, None)


def start_compilation(project_id, verilog_sources, components):
    # only one build per project at a time
    if project_id in running_threads:
        if not running_threads[project_id].is_alive():
            running_threads.pop(project_id)
        else:
            raise CompileError("A build is already running for this project")

    log_queue = Queue()
    log_queue.progress = 1
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
        raise CompileError("There is no build currently running for this project")
