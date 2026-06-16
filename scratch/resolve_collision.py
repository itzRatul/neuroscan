from huggingface_hub import HfApi

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)

chat_repo = "itzRatul/neuroscan-chat-backend"

print("Deleting colliding secrets from Space...")
colliding_keys = ["GROQ_MODEL", "MAIN_BACKEND_URL"]

for key in colliding_keys:
    try:
        api.delete_space_secret(repo_id=chat_repo, key=key)
        print(f"  ✅ Deleted secret: {key}")
    except Exception as e:
        print(f"  ❌ Error deleting secret {key}: {e}")

print("\nVerifying current config...")
try:
    secrets = api.get_space_secrets(repo_id=chat_repo)
    print("Secrets:", list(secrets.keys()))
except Exception as e:
    print(f"Error listing secrets: {e}")

try:
    variables = api.get_space_variables(repo_id=chat_repo)
    print("Variables:", {k: v.value for k, v in variables.items()})
except Exception as e:
    print(f"Error listing variables: {e}")
