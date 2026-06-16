from huggingface_hub import HfApi

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)
repo_id = "itzRatul/neuroscan-backend"

try:
    runtime = api.get_space_runtime(repo_id=repo_id)
    print(f"Stage: {runtime.stage}")
except Exception as e:
    print(f"Error: {e}")
