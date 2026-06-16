from huggingface_hub import fetch_space_logs

HF_TOKEN = "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"
repo_id = "itzRatul/neuroscan-chat-backend"

print(f"Fetching logs for: {repo_id}")
try:
    # We fetch the current buffered logs (follow=False)
    logs_gen = fetch_space_logs(repo_id=repo_id, token=HF_TOKEN, follow=False)
    lines = list(logs_gen)
    print("--- Last 100 lines of runtime logs ---")
    for line in lines[-100:]:
        print(line, end="")
except Exception as e:
    print(f"Error fetching logs: {e}")
