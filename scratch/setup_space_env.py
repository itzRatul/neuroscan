from huggingface_hub import HfApi

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)

# 1. Config for neuroscan-chat-backend
chat_repo = "itzRatul/neuroscan-chat-backend"
chat_secrets = {
    "TELEGRAM_BOT_TOKEN": "8999930472:AAFebi5BXlOVaqARa1s2RM3O7J0DO9sLU_E",
    "TAVILY_API_KEY": "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",
    "GROQ_API_KEY": "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",
    "GROQ_API_KEY_2": "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",
    "GROQ_API_KEY_3": "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",
    "GROQ_API_KEY_4": "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"
}
chat_variables = {
    "GROQ_MODEL": "llama-3.3-70b-versatile",
    "MAIN_BACKEND_URL": "https://itzratul-neuroscan-backend.hf.space"
}

print(f"Setting up Secrets and Variables for: {chat_repo}")
for k, v in chat_secrets.items():
    try:
        api.add_space_secret(repo_id=chat_repo, key=k, value=v)
        print(f"  ✅ Added secret: {k}")
    except Exception as e:
        print(f"  ❌ Error adding secret {k}: {e}")

for k, v in chat_variables.items():
    try:
        api.add_space_variable(repo_id=chat_repo, key=k, value=v)
        print(f"  ✅ Added variable: {k} = {v}")
    except Exception as e:
        print(f"  ❌ Error adding variable {k}: {e}")

# 2. Config for neuroscan-backend
backend_repo = "itzRatul/neuroscan-backend"
backend_variables = {
    "CHAT_BACKEND_URL": "https://itzratul-neuroscan-chat-backend.hf.space"
}

print(f"\nSetting up Variables for: {backend_repo}")
for k, v in backend_variables.items():
    try:
        api.add_space_variable(repo_id=backend_repo, key=k, value=v)
        print(f"  ✅ Added variable: {k} = {v}")
    except Exception as e:
        print(f"  ❌ Error adding variable {k}: {e}")

print("\n🎉 Environment setup complete for both spaces!")
