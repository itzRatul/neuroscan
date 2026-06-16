from huggingface_hub import fetch_space_logs

HF_TOKEN = "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"
repo_id = "itzRatul/neuroscan-backend"

print(f"Fetching build logs for: {repo_id}")
try:
    logs_gen = fetch_space_logs(repo_id=repo_id, token=HF_TOKEN, build=True, follow=False)
    lines = list(logs_gen)
    print("--- Last 100 lines of build logs ---")
    for line in lines[-100:]:
        print(line, end="")
except Exception as e:
    print(f"Error fetching logs: {e}")
