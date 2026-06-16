import requests
import json

bot_token = "8999930472:AAFebi5BXlOVaqARa1s2RM3O7J0DO9sLU_E"
chat_id = 123456

url = f"https://api.telegram.org/bot{bot_token}/sendChatAction"
payload = {
    "chat_id": chat_id,
    "action": "typing"
}

print(f"Sending POST to: {url}")
try:
    r = requests.post(url, json=payload, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
