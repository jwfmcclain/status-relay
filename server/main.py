import sys
import os
import urllib.parse
import json
import tempfile
import shutil
import traceback
import dataclasses

from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

host_name = ''

def float_or_none(v):
    return float(v) if v is not None else None

@dataclass
class JobState:
    topic: str
    message: str
    state: str
    current_z: float
    max_z: float
    estimated_print_time: int
    percent_done: float
    elapsed_print_time: int
    current_time: int

    def update(self, data):
        self.topic = data['topic']
        self.message = data['message']
        self.state = data['state']['text']
        self.current_z = float_or_none(data['currentZ'])

        if 'analysis' in data['meta']:
            self.max_z = data['meta']['analysis']['printingArea']['maxZ']
            self.estimated_print_time = float_or_none(data['meta']['analysis']['estimatedPrintTime'])
        else:
            self.max_z = None
            self.estimated_print_time = None

        self.percent_done = float(data['progress']['completion']) if data['currentZ'] is not None else None
        self.elapsed_print_time = data['progress']['printTime']
        self.current_time = int(data['currentTime'])


def init_job_state():
    new_state = JobState(None, None, None,
                         None, None, None,
                         None, None, None)

    try:
        with open("last_status.json", mode='rb') as f:
            raw_data = f.read()
        data = json.loads(raw_data.decode('utf8'))
        new_state.update(data)
        print("loaded last_status.json")
        print(new_state)
    except:
        print("Can't read last_status.json")
        print(traceback.format_exc())

    return new_state

job_state = init_job_state()

class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        pp = urllib.parse.urlparse(self.path)
        path = pp.path

        if path == "/update":
            content_length = int(self.headers['Content-Length'])
            raw_data = self.rfile.read(content_length)

            try:
                with open("platform/logs/statuses", mode="at") as f:
                    f.write(f"{str(datetime.utcnow())}\n")
                    f.write(f"{raw_data.decode('utf8')}\n")
            except UnicodeDecodeError as e:
                print(raw_data, file=sys.stderr)
                self.send_error(400, f"{e}")
                return

            try:
                data = json.loads(raw_data.decode('utf8'))
            except json.decoder.JSONDecodeError as e:
                print(raw_data, file=sys.stderr)
                self.send_error(400, f"{e}")
                return

            # Persist so we have something if we get rebooted
            fd, f_name = tempfile.mkstemp(prefix="new-status-", suffix=".json", dir=os.getcwd())
            f = os.fdopen(fd, mode='wb')
            f.write(raw_data)
            f.close()
            os.replace(f_name, "last_status.json")

            job_state.update(data)

            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404, f"unknown: {path}")

    def write_text_status(self):
        self.wfile.write(bytes(f"{job_state.message} ({job_state.state})\n", "utf-8"))
        if job_state.topic == 'Print Started':
            self.wfile.write(bytes(f"Print hight: {job_state.max_z}\n", "utf-8"))
            self.wfile.write(bytes(f"Estimated Time: {job_state.estimated_print_time}\n", "utf-8"))
        elif job_state.topic == 'Print Progress':
            self.wfile.write(bytes(f"Percent Done {job_state.percent_done:.1f}%\n", "utf-8"))

            self.wfile.write(bytes(f"Print height: {job_state.max_z} Current: {job_state.current_z}", "utf-8"))
            if job_state.max_z is not None and job_state.current_z is not None:
                self.wfile.write(bytes(f" ({(job_state.current_z / job_state.max_z):.1%})\n", "utf-8"))
            else:
                self.wfile.write(bytes("\n", "utf-8"))

            self.wfile.write(bytes(f"Estimated Time: {job_state.estimated_print_time} Elapsed: {job_state.elapsed_print_time}", "utf-8"))
            if job_state.estimated_print_time is not None and job_state.elapsed_print_time is not None:
                self.wfile.write(bytes(f" (delta: {job_state.estimated_print_time - job_state.elapsed_print_time})\n", "utf-8"))
            else:
                self.wfile.write(bytes("\n", "utf-8"))
        elif job_state.topic == 'Print Done':
            self.wfile.write(bytes(f"Estimated Time: {job_state.estimated_print_time} Actual: {job_state.elapsed_print_time}\n", "utf-8"))
        else:
            self.wfile.write(bytes(f"{job_state}\n", "utf-8"))


    def do_GET(self):
        pp = urllib.parse.urlparse(self.path)
        path = pp.path
        params = urllib.parse.parse_qs(pp.query)

        if path == "/":
            accepting = tuple()
            if 'accept' in self.headers:
                accepting = self.headers['accept'].split(',')

            self.send_response(200)

            if 'application/json' in accepting:
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = dataclasses.asdict(job_state)
                self.wfile.write(bytes(json.dumps(data), "utf-8"))
            else:
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.write_text_status()
        else:
            self.send_error(404, f"unknown: {path}")

if __name__ == "__main__":
    server_port = int(sys.argv[1])

    webServer = ThreadingHTTPServer((host_name, server_port), MyServer)
    print("Server started http://%s:%s" % (host_name, server_port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped")
