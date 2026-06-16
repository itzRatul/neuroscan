"""
NeuroScan — HuggingFace Space Deployment Script
================================================
Uploads backend/ → itzRatul/neuroscan-backend
Uploads chat_backend/ → itzRatul/neuroscan-ai-chat
"""

import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete

HF_TOKEN = "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"
api = HfApi(token=HF_TOKEN)

BASE = Path(__file__).parent

# ─────────────────────────────────────────────────────────────
# BACKEND → neuroscan-backend
# ─────────────────────────────────────────────────────────────

BACKEND_REPO = "itzRatul/neuroscan-backend"
BACKEND_DIR  = BASE / "backend"

# Files/dirs to SKIP (never upload)
BACKEND_SKIP = {".venv", "__pycache__", "results", ".git",
                "ai_chat_backend.log", "photo_scan_backend.log",
                "webapp.log", "start_servers.sh"}

BACKEND_README = """\
---
title: NeuroScan Backend API
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# NeuroScan Backend API

Face analysis API — upload a face photo and get stroke risk prediction.

## Endpoints
- `POST /analyze` — main analysis (face scan → ML model → PDF report)
- `GET  /health`  — health check
- `GET  /results/{id}/{file}` — serve annotated images and PDFs
"""

def collect_backend_files():
    ops = []
    for path in BACKEND_DIR.rglob("*"):
        if path.is_dir():
            continue
        # Skip unwanted
        parts = path.parts
        if any(skip in parts for skip in BACKEND_SKIP):
            continue
        rel = path.relative_to(BACKEND_DIR)
        ops.append(CommitOperationAdd(
            path_in_repo=str(rel),
            path_or_fileobj=str(path),
        ))
        print(f"  [backend] + {rel}")
    # Override README
    ops.append(CommitOperationAdd(
        path_in_repo="README.md",
        path_or_fileobj=BACKEND_README.encode(),
    ))
    print(f"  [backend] + README.md (overwritten)")
    return ops


# ─────────────────────────────────────────────────────────────
# CHAT BACKEND → neuroscan-ai-chat
# ─────────────────────────────────────────────────────────────

CHAT_REPO = "itzRatul/neuroscan-ai-chat"
CHAT_DIR  = BASE / "chat_backend"

CHAT_SKIP = {".venv", "__pycache__", ".git", ".env"}

CHAT_README = """\
---
title: NeuroScan AI Chat
emoji: 🤖
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# NeuroScan AI Chat Backend

LLM-powered chat + Telegram bot for NeuroScan stroke risk assistant.

## Features
- Telegram bot webhook (`/webhook/telegram`)
- Conversational AI with session memory
- Web search integration (Tavily)
- Syncs with neuroscan-backend for analysis results
"""

def collect_chat_files():
    ops = []
    for path in CHAT_DIR.rglob("*"):
        if path.is_dir():
            continue
        parts = path.parts
        if any(skip in parts for skip in CHAT_SKIP):
            continue
        rel = path.relative_to(CHAT_DIR)
        ops.append(CommitOperationAdd(
            path_in_repo=str(rel),
            path_or_fileobj=str(path),
        ))
        print(f"  [chat] + {rel}")
    # Override README
    ops.append(CommitOperationAdd(
        path_in_repo="README.md",
        path_or_fileobj=CHAT_README.encode(),
    ))
    print(f"  [chat] + README.md (overwritten)")
    return ops


# ─────────────────────────────────────────────────────────────
# DELETE old files from a space
# ─────────────────────────────────────────────────────────────

def get_existing_files(repo_id):
    try:
        files = api.list_repo_files(repo_id=repo_id, repo_type="space")
        return [f for f in files if f != ".gitattributes"]
    except Exception as e:
        print(f"  Warning: could not list files for {repo_id}: {e}")
        return []


def deploy(repo_id, collect_fn, label):
    print(f"\n{'='*60}")
    print(f"Deploying: {label} → {repo_id}")
    print(f"{'='*60}")

    # 1. List existing files to delete
    existing = get_existing_files(repo_id)
    delete_ops = [CommitOperationDelete(path_in_repo=f) for f in existing]
    print(f"  Will delete {len(delete_ops)} old file(s): {existing}")

    # 2. Collect new files
    print("  Collecting new files...")
    add_ops = collect_fn()
    print(f"  Will upload {len(add_ops)} file(s)")

    # 3. Commit everything in one shot
    all_ops = delete_ops + add_ops
    print("  Committing to HF Space...")
    url = api.create_commit(
        repo_id=repo_id,
        repo_type="space",
        operations=all_ops,
        commit_message=f"feat: deploy {label} — full reset",
    )
    print(f"  ✅ Done! Commit: {url}")
    return url


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "both"

    if target in ("backend", "both"):
        deploy(BACKEND_REPO, collect_backend_files, "neuroscan-backend")

    if target in ("chat", "both"):
        deploy(CHAT_REPO, collect_chat_files, "neuroscan-ai-chat")

    print("\n🎉 All deployments complete!")
    print(f"  backend : https://itzratul-neuroscan-backend.hf.space/health")
    print(f"  chat    : https://itzratul-neuroscan-ai-chat.hf.space/health")
