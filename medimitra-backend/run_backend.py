import subprocess
import sys

print("Starting MediMitra Backend on port 8001...")
print("API docs at http://localhost:8001/docs")
print("Press Ctrl+C to stop\n")

subprocess.run([
    sys.executable, "-m", "uvicorn",
    "main:app",
    "--reload",
    "--port", "8001"
])