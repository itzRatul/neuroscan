import requests

url = "https://itzratul-neuroscan-chat-backend.hf.space/webhook/telegram"

payload = {
    "message": {
        "chat": {
            "id": 123456
        },
        "text": "/start"
    }
}

print(f"Sending mock /start webhook request to: {url}")
try:
    r = requests.post(url, json=payload, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
