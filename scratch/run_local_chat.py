import os
import sys
import subprocess
import time
import re
import requests

# Kill existing tunnel and uvicorn processes to start fresh
print("Cleaning up old tunnel and uvicorn processes...")
subprocess.run("pkill -f pinggy", shell=True)
subprocess.run("pkill -f \"ssh.*pinggy.io\"", shell=True)
subprocess.run("pkill -f \"uvicorn.*8001\"", shell=True)
subprocess.run("fuser -k 8001/tcp", shell=True)
time.sleep(3)

# Find virtualenv python
venv_python = "/home/itzratul/Github/neuroscan/backend/.venv/bin/python3"
if not os.path.exists(venv_python):
    venv_python = "python3"

print(f"Using python executable: {venv_python}")

# 1. Start local chat backend (Uvicorn)
chat_dir = "/home/itzratul/Github/neuroscan/chat_backend"
print("Starting local chat backend on port 8001...")
chat_log = open("/home/itzratul/Github/neuroscan/scratch/local_chat.log", "w")
chat_proc = subprocess.Popen(
    [venv_python, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"],
    cwd=chat_dir,
    stdout=chat_log,
    stderr=subprocess.STDOUT
)

# 2. Start Pinggy SSH Tunnel
print("Starting Pinggy SSH tunnel...")
tunnel_log_path = "/home/itzratul/Github/neuroscan/scratch/local_pinggy.log"
tunnel_log = open(tunnel_log_path, "w")
tunnel_proc = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-p", "443", "-R0:localhost:8001", "qr@a.pinggy.io"],
    stdout=tunnel_log,
    stderr=subprocess.STDOUT
)

# 3. Read Pinggy URL from logs
print("Waiting for Pinggy public HTTPS URL...")
public_url = None
for _ in range(30):
    time.sleep(1)
    if os.path.exists(tunnel_log_path):
        with open(tunnel_log_path, "r") as f:
            content = f.read()
            matches = re.findall(r"https://[a-zA-Z0-9\.\-]+free\.link|https://[a-zA-Z0-9\.\-]+pinggy\.net", content)
            if matches:
                public_url = matches[0]
                break

if not public_url:
    print("❌ Failed to obtain public tunnel URL from Pinggy. Log contents:")
    if os.path.exists(tunnel_log_path):
        with open(tunnel_log_path, "r") as f:
            print(f.read())
    sys.exit(1)

print(f"✅ Public Tunnel URL: {public_url}")

# 4. Register Webhook with Telegram
bot_token = "8999930472:AAFebi5BXlOVaqARa1s2RM3O7J0DO9sLU_E"
webhook_url = f"{public_url}/webhook/telegram"
print(f"Registering webhook: {webhook_url}")
reg_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
try:
    resp = requests.post(reg_url, json={"url": webhook_url})
    print(f"Telegram response: {resp.json()}")
except Exception as e:
    print(f"❌ Error registering webhook: {e}")

# Keep script running to maintain tunnel and backend, monitor logs
print("\n🔥 Local Chat Backend and Tunnel are RUNNING!")
print("Monitor chat logs with: tail -f scratch/local_chat.log")
print("Press Ctrl+C to terminate.")

try:
    while True:
        # Check if processes are still running
        if chat_proc.poll() is not None:
            print("❌ Chat backend process terminated unexpectedly!")
            break
        if tunnel_proc.poll() is not None:
            print("❌ Tunnel process terminated unexpectedly!")
            break
        time.sleep(2)
except KeyboardInterrupt:
    print("\nShutting down processes...")
finally:
    chat_proc.terminate()
    tunnel_proc.terminate()
    chat_log.close()
    tunnel_log.close()
    print("Cleanup done. Bye!")
