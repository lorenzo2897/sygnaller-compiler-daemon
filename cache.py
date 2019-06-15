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
    import shutil
    shutil.rmtree(cache_dir + project_id, True)


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


def write_outer_axi_wrapper(project_id, name, source_code):
    write_axi_wrapper(project_id, name + '.outer', source_code)


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


def get_python_api_path(project_id):
    os.makedirs(cache_dir + project_id + '/out', exist_ok=True)
    return cache_dir + project_id + '/out/sygnaller.py'


def get_report_path(project_id):
    os.makedirs(cache_dir + project_id + '/out', exist_ok=True)
    return cache_dir + project_id + '/out/build_report.txt'


def get_build_report(project_id):
    try:
        with open(get_report_path(project_id)) as f:
            last_build_status = f.readline()
            build_report = f.read()
    except:
        last_build_status = ''
        build_report = ''
    return last_build_status, build_report


def put_source_mapping(project_id, mapping):
    try:
        with open(cache_dir + project_id + '/source_mapping.json', 'w') as f:
            json.dump(mapping, f)
    except:
        pass


def get_source_mapping(project_id):
    try:
        with open(cache_dir + project_id + '/source_mapping.json') as f:
            return json.load(f)
    except:
        return []


def get_overlay_modified_date(project_id):
    bitfile = get_overlay_bit_path(project_id)
    tclfile = get_overlay_tcl_path(project_id)
    if os.path.exists(bitfile) and os.path.exists(tclfile):
        return max(os.path.getmtime(bitfile), os.path.getmtime(tclfile))
    else:
        return 0


# *****************************************
# Unit tests
# *****************************************

import unittest


class TestCache(unittest.TestCase):
    test_id = '_test_dummy'

    def test_exists(self):
        import shutil
        shutil.rmtree(cache_dir + self.test_id, True)
        self.assertFalse(project_exists(self.test_id))

    def test_create(self):
        import shutil
        shutil.rmtree(cache_dir + self.test_id, True)
        write_cache(self.test_id, [])
        self.assertTrue(project_exists(self.test_id))

    def test_write_read(self):
        components = [
            {"name": "c1"},
            {"name": "c1"}
        ]
        write_cache(self.test_id, components)
        self.assertEqual(components, cached_components(self.test_id))

    def test_clear(self):
        write_cache(self.test_id, [])
        self.assertTrue(project_exists(self.test_id))
        clear_cache(self.test_id)
        self.assertFalse(project_exists(self.test_id))

    def test_axi_write(self):
        write_axi_wrapper(self.test_id, 'testwrap', 'blah')
        fp = os.path.join(get_wrappers_dir(self.test_id), 'testwrap')
        self.assertTrue(os.path.exists(fp))
        clear_axi_wrappers(self.test_id)
        self.assertFalse(os.path.exists(fp))

    def test_axi_outer_write(self):
        write_outer_axi_wrapper(self.test_id, 'testwrap', 'blah')
        fp = os.path.join(get_wrappers_dir(self.test_id), 'testwrap.outer')
        self.assertTrue(os.path.exists(fp))
        clear_axi_wrappers(self.test_id)
        self.assertFalse(os.path.exists(fp))

    def test_source_mapping(self):
        m = {"a": "b"}
        write_cache(self.test_id, [])
        put_source_mapping(self.test_id, m)
        self.assertEqual(get_source_mapping(self.test_id), m)

    def test_source_mapping_missing(self):
        self.assertEqual(get_source_mapping('_not_exists'), [])

    def test_modified_date_missing(self):
        self.assertEqual(get_overlay_modified_date('_not_exists'), 0)


if __name__ == '__main__':
    unittest.main()
