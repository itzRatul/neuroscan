import os
import sys
import json
import requests
from huggingface_hub import HfApi, constants
from huggingface_hub.utils import build_hf_headers, get_session, hf_raise_for_status

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)

repos = ["itzRatul/neuroscan-backend", "itzRatul/neuroscan-chat-backend"]

def get_space_logs(space_id: str, level: str = "run", token: str = None):
    try:
        # 1. Fetch a JWT token to access the Space API
        jwt_url = f"{constants.ENDPOINT}/api/spaces/{space_id}/jwt"
        response = get_session().get(jwt_url, headers=build_hf_headers(token=token))
        hf_raise_for_status(response)
        jwt_token = response.json()["token"]

        # 2. Stream the logs via SSE using requests
        logs_url = f"https://api.hf.space/v1/{space_id}/logs/{level}"
        logs = []
        headers = build_hf_headers(token=jwt_token)
        response = requests.get(logs_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        # Read a chunk or read lines up to a limit
        count = 0
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                line_data = line[len(b"data: "):]
                try:
                    event = json.loads(line_data.decode())
                    msg = event.get('data', '')
                    if msg:
                        logs.append(msg.strip())
                        count += 1
                        if count > 200:
                            break
                except json.JSONDecodeError:
                    continue
        return "\n".join(logs)
    except Exception as e:
        return f"Error fetching {level} logs: {e}"

for repo in repos:
    print(f"\n=========================================")
    print(f"Checking Space: {repo}")
    print(f"=========================================")
    try:
        runtime = api.get_space_runtime(repo_id=repo)
        print(f"Stage: {runtime.stage}")
        print(f"Hardware: {runtime.hardware}")
    except Exception as e:
        print(f"Error fetching runtime info: {e}")
        
    print("\n--- Space Build Logs ---")
    print(get_space_logs(repo, "build", HF_TOKEN))

    print("\n--- Space Run Logs ---")
    print(get_space_logs(repo, "run", HF_TOKEN))
