import requests

HF_TOKEN = "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"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

urls = [
    "https://itzratul-neuroscan-chat-backend.hf.space/",
    "https://itzratul-neuroscan-chat-backend.hf.space/health"
]

for url in urls:
    print(f"\nRequesting with Auth: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error requesting {url}: {e}")
