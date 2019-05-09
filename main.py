#!/usr/bin/env python3

import http.server
import urllib.parse
import json
import traceback

import compile
import cache
from component import ComponentSpec


class DaemonServer(http.server.BaseHTTPRequestHandler):

    def _error(self, err):
        return {
            'error': err
        }

    def api(self, command, data):
        if command == 'echo':
            return data

        elif command == 'clear_cache':
            cache.clear_cache(data['project_id'])
            return {}

        elif command == 'compile':
            project_id = data['project_id']
            sources = data['sources']
            components = [ComponentSpec(c['name'], c['ports']) for c in data['components']]
            compile.start_compilation(project_id, sources, components)
            return {}

        elif command == 'build_progress':
            project_id = data['project_id']
            logs = []

            if project_id in compile.running_logs:
                while not compile.running_logs[project_id].empty():
                    logs.append(compile.running_logs[project_id].get_nowait())

            return {
                "running": project_id in compile.running_threads,
                "last_completed": cache.get_overlay_modified_date(project_id),
                "logs": '\n'.join(logs)
            }

        elif command == 'cancel_build':
            project_id = data['project_id']
            compile.cancel_compilation(project_id)

        elif command == 'download_overlay_bit':
            project_id = data['project_id']
            return {"file": cache.get_overlay_bit_path(project_id)}

        elif command == 'download_overlay_tcl':
            project_id = data['project_id']
            return {"file": cache.get_overlay_tcl_path(project_id)}

        else:
            return self._error('Command not supported')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()


    def do_GET(self):
        try:
            command = urllib.parse.urlparse(self.path).path[1:]
            resp = self.api(command, {})
        except KeyError:
            resp = self._error('Missing data (use POST)')
        except Exception as e:
            print(type(e).__name__, e)
            resp = self._error('Server error')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(resp), encoding='utf-8'))
        self.wfile.write(b'\n')


    def do_POST(self):
        command = ''
        try:
            url_string = urllib.parse.urlparse(self.path)
            d_length = int(self.headers['content-length'])

            command = url_string.path[1:]
            if d_length == 0:
                data = None
            else:
                data = json.loads(self.rfile.read(d_length))

            resp = self.api(command, data)

        except json.decoder.JSONDecodeError:
            resp = self._error('Invalid JSON')

        except KeyError:
            resp = self._error('Missing data')

        except compile.CompileError as e:
            resp = self._error(str(e.args[0]))

        except Exception as e:
            print(type(e).__name__, e)
            traceback.print_exc()
            resp = self._error('Server error (%s encountered %s)' % (command, type(e).__name__))

        if 'file' in resp:
            try:
                with open(resp['file'], 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                    self.end_headers()
                    self.wfile.write(f.read())
            except IOError:
                self.send_error(404, 'File Not Found')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(resp), encoding='utf-8'))
            self.wfile.write(b'\n')


def start_server(port=9000):
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, DaemonServer)
    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()


if __name__ == '__main__':
    start_server()
