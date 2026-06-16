import os
import time
import logging
from pathlib import Path
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from the same directory as this file (chat_backend/.env)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
logger = logging.getLogger("ChatBackend")

class GrokKeyManager:
    def __init__(self):
        self.keys = []

        # Format 1: GROQ_API_KEY (first key), GROQ_API_KEY_2, GROQ_API_KEY_3, ...
        first_key = os.getenv("GROQ_API_KEY", "").strip()
        if first_key:
            self.keys.append(first_key)
        i = 2
        while True:
            key = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
            if not key:
                break
            self.keys.append(key)
            i += 1

        # Format 2: GROQ_API_KEY_1, GROQ_API_KEY_2 (numbered from 1)
        if not self.keys:
            i = 1
            while True:
                key = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
                if not key:
                    break
                self.keys.append(key)
                i += 1

        # Format 3: GROK_API_KEYS="key1,key2" (old comma-separated format)
        if not self.keys:
            keys_env = os.getenv("GROK_API_KEYS", "").strip()
            if keys_env:
                self.keys = [k.strip() for k in keys_env.split(",") if k.strip()]

        # Track blocked keys: key -> unblock_timestamp
        self.blocked_keys = {}
        self.current_index = 0

        if not self.keys:
            logger.warning("No Groq API keys found! Set GROQ_API_KEY_1 or GROK_API_KEYS in .env")
        else:
            logger.info(f"Loaded {len(self.keys)} Groq API key(s).")

    def get_next_key(self) -> Optional[str]:
        if not self.keys:
            return None

        start_index = self.current_index
        while True:
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)

            if key in self.blocked_keys:
                if time.time() >= self.blocked_keys[key]:
                    del self.blocked_keys[key]
                    return key
            else:
                return key

            if self.current_index == start_index:
                logger.error("ALL Groq API keys are currently rate-limited!")
                return None

    def block_key(self, key: str):
        block_duration = 60 * 60  # Block for 1 hour (Groq resets faster than 24h)
        unblock_time = time.time() + block_duration
        self.blocked_keys[key] = unblock_time
        logger.warning(f"Key {key[:8]}... rate-limited. Blocked for 1 hour.")


class LLMManager:
    def __init__(self):
        self.key_manager = GrokKeyManager()
        # Groq's OpenAI-compatible endpoint
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"LLM: {self.model} via {self.base_url}")

    def generate_response(self, system_prompt: str, chat_history: List[dict], user_message: str, retries: int = 2) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        for attempt in range(retries + 1):
            key = self.key_manager.get_next_key()
            if not key:
                return "I'm sorry, but our services are currently overloaded. Please try again later."

            client = OpenAI(api_key=key, base_url=self.base_url)

            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                )
                return response.choices[0].message.content

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg or "rate_limit" in error_msg:
                    logger.warning(f"Rate limit hit for key {key[:8]}...")
                    self.key_manager.block_key(key)
                    continue
                else:
                    logger.error(f"Groq API error: {e}")
                    return "I encountered an error while trying to process your request."

        return "I'm sorry, but our services are currently overloaded. Please try again later."
