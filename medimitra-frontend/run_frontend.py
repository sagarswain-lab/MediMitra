import http.server
import socketserver
import webbrowser
import threading
import os

PORT = 5500
FILE = "MediMitra_SPA.html"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    webbrowser.open(f"http://localhost:{PORT}/{FILE}")

# Open browser after 1 second
threading.Timer(1.0, open_browser).start()

print(f" MediMitra Frontend running at http://localhost:{PORT}/{FILE}")
print(" Opening browser automatically...")
print("Press Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
    httpd.serve_forever()