"""
AI Provider Abstraction
------------------------
A single, thin interface the rest of the app calls instead of talking to any
specific LLM vendor. Configured entirely through environment variables
(see app/core/config.py) — never hardcode a key.

    AI_PROVIDER=gemini|openai|none
    AI_API_KEY=...
    AI_MODEL=...

Every caller in this codebase MUST treat `generate_json` as fallible: on
timeout, missing key, rate limit, or malformed output, it returns None and
the caller is expected to fall back to its existing deterministic logic.
Nothing in Gradustry should crash because the AI provider is unreachable.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("gradustry.ai")


@dataclass
class AIResult:
    raw_text: str
    model: str
    provider: str


class AIProvider:
    """Vendor-agnostic async LLM client with retries + timeout + safe failure."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self.max_retries = settings.AI_MAX_RETRIES

    def is_configured(self) -> bool:
        return bool(self.provider in ("gemini", "openai") and self.api_key)

    async def generate(self, prompt: str, system_prompt: str = "") -> Optional[AIResult]:
        """Returns None on any failure — callers must have a fallback path."""
        if not self.is_configured():
            logger.info("AI provider not configured — skipping call, caller should fall back.")
            return None

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.provider == "gemini":
                    text = await self._call_gemini(prompt, system_prompt)
                elif self.provider == "openai":
                    text = await self._call_openai(prompt, system_prompt)
                else:
                    return None
                return AIResult(raw_text=text, model=self.model, provider=self.provider)
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as e:
                last_error = e
                logger.warning(f"AI call attempt {attempt + 1} failed: {e}")
            except Exception as e:  # noqa: BLE001 - AI calls must never bubble up as 500s
                last_error = e
                logger.error(f"Unexpected AI provider error: {e}")
                break

        logger.warning(f"AI provider unavailable after retries: {last_error}. Falling back.")
        return None

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Optional[dict]:
        """Like generate(), but parses the response as JSON. Returns None on any failure."""
        result = await self.generate(prompt, system_prompt)
        if result is None:
            return None
        text = result.raw_text.strip()
        # LLMs love wrapping JSON in ```json fences — strip them defensively.
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("AI response was not valid JSON — falling back.")
            return None

    async def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_openai(self, prompt: str, system_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "temperature": 0.4, "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


ai_provider = AIProvider()
