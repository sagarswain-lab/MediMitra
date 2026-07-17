import http.server
import socketserver
import webbrowser
import threading
import os
import subprocess
import sys

PORT = 5500
FILE = "medimitra_spa.html"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def free_port(port):
    try:
        # Check netstat for the port on Windows or netstat/lsof on others
        if sys.platform == 'win32':
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.strip().split('\n'):
                parts = line.strip().split()
                if len(parts) >= 5 and parts[1].endswith(f":{port}"):
                    pid = int(parts[-1])
                    if pid > 0 and pid != os.getpid():
                        print(f" Port {port} is occupied by process {pid}. Terminating it...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            output = subprocess.check_output(f"lsof -t -i:{port}", shell=True).decode()
            for pid_str in output.strip().split('\n'):
                if pid_str:
                    pid = int(pid_str)
                    if pid != os.getpid():
                        print(f" Port {port} is occupied by process {pid}. Terminating it...")
                        os.kill(pid, 9)
    except Exception:
        pass

def open_browser():
    webbrowser.open(f"http://localhost:{PORT}/{FILE}")

# Free the port if it's already in use
free_port(PORT)

# Open browser after 1 second
threading.Timer(1.0, open_browser).start()

print(f" MediMitra Frontend running at http://localhost:{PORT}/{FILE}")
print(" Opening browser automatically...")
print("Press Ctrl+C to stop")

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

with ReusableTCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
    httpd.serve_forever()

