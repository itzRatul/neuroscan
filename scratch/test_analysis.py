import requests
import os

url = "https://itzratul-neuroscan-backend.hf.space/analyze"
img_path = "/home/itzratul/Github/neuroscan/webapp/assets/Formal photo.png"

if not os.path.exists(img_path):
    img_path = "/home/itzratul/Github/neuroscan/backend/.venv/lib/python3.12/site-packages/matplotlib/mpl-data/sample_data/grace_hopper.jpg"

print(f"Reading image bytes from: {img_path}")
with open(img_path, "rb") as f:
    img_data = f.read()

print(f"Uploading image bytes (size: {len(img_data)} bytes) to: {url}")
try:
    files = {"file": ("photo.jpg", img_data, "image/jpeg")}
    data = {"session_id": "test_session_123"}
    r = requests.post(url, files=files, data=data, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
