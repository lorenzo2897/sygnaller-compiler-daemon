import os
import json

cache_dir = "/home/ubuntu/compiler_cache/"


def project_exists(project_id):
    return os.path.exists(cache_dir + project_id + "/cache.json")


def cached_components(project_id):
    with open(cache_dir + project_id + "/cache.json") as f:
        a = json.load(f)
    return a


def write_cache(project_id, component_names):
    os.makedirs(cache_dir + project_id, exist_ok=True)
    with open(cache_dir + project_id + "/cache.json", 'w') as f:
        json.dump(component_names, f)


def clear_cache(project_id):
    try:
        os.remove(cache_dir + project_id + "/cache.json")
    except OSError:
        pass


def clear_axi_wrappers(project_id):
    os.makedirs(cache_dir + project_id + '/wrappers', exist_ok=True)
    for the_file in os.listdir(cache_dir + project_id + '/wrappers'):
        try:
            file_path = os.path.join(cache_dir + project_id + '/wrappers', the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def write_axi_wrapper(project_id, name, source_code):
    os.makedirs(cache_dir + project_id + '/wrappers', exist_ok=True)
    with open(cache_dir + project_id + "/wrappers/" + name, 'w') as f:
        f.write(source_code)


def write_tcl_script(project_id, source_code):
    os.makedirs(cache_dir + project_id, exist_ok=True)
    with open(cache_dir + project_id + "/script.tcl", 'w') as f:
        f.write(source_code)


def get_wrappers_dir(project_id):
    return cache_dir + project_id + '/wrappers'


def get_script_path(project_id):
    return cache_dir + project_id + '/script.tcl'


def get_overlay_bit_path(project_id):
    os.makedirs(cache_dir + project_id + '/out', exist_ok=True)
    return cache_dir + project_id + '/out/overlay.tcl'


def get_overlay_tcl_path(project_id):
    os.makedirs(cache_dir + project_id + '/out', exist_ok=True)
    return cache_dir + project_id + '/out/overlay.bit'


def get_overlay_modified_date(project_id):
    bitfile = get_overlay_bit_path(project_id)
    tclfile = get_overlay_tcl_path(project_id)
    if os.path.exists(bitfile) and os.path.exists(tclfile):
        return max(os.path.getmtime(bitfile), os.path.getmtime(tclfile))
    else:
        return 0
