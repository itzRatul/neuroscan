from huggingface_hub import HfApi

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)

chat_repo = "itzRatul/neuroscan-chat-backend"

print("--- Secrets ---")
try:
    secrets = api.get_space_secrets(repo_id=chat_repo)
    print(secrets)
except Exception as e:
    print(f"Error getting secrets: {e}")

print("\n--- Variables ---")
try:
    variables = api.get_space_variables(repo_id=chat_repo)
    print(variables)
except Exception as e:
    print(f"Error getting variables: {e}")
