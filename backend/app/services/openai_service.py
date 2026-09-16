"""
===========================================================
LLM Service (OpenAI-SDK compatible)
-----------------------------------------------------------
Thin, reusable wrapper around the official OpenAI SDK
(pip install openai). By default this points at Groq's free,
OpenAI-compatible endpoint (console.groq.com) - no billing
setup required. To use real OpenAI instead, just set
OPENAI_BASE_URL=https://api.openai.com/v1 and a paid key in
.env. Every agent that needs an LLM call (Extraction,
Recovery, Conversation) goes through this single service, so
the provider only needs to be changed in one place.
===========================================================
"""

import time

from app.config import settings
from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class OpenAIService:

    def __init__(self):
        if OpenAI is None:
            raise RuntimeError(
                "openai package is not installed. Run: pip install openai"
            )

        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "YOUR_API_KEY_HERE":
            logger.warning(
                "OPENAI_API_KEY is not set. Set it in your .env file before calling OpenAI."
            )

        # The SDK also auto-reads OPENAI_API_KEY from the environment,
        # but we pass it explicitly so config.py stays the single source of truth.
        # base_url defaults to Groq's free, OpenAI-compatible endpoint.
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
        self.model = settings.OPENAI_MODEL

    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant for OrdEasy.", retries: int = 2) -> str:
        """
        Calls OpenAI chat completions with basic retry on transient failures.
        Returns the raw text response.
        """

        last_error = None

        for attempt in range(1, retries + 2):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                return completion.choices[0].message.content

            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI call failed (attempt {attempt}): {e}")
                time.sleep(1.5 * attempt)

        logger.error(f"OpenAI call failed after retries: {last_error}")
        raise RuntimeError(f"OpenAI request failed: {last_error}")


_openai_singleton = None


def get_openai_service() -> "OpenAIService":
    global _openai_singleton
    if _openai_singleton is None:
        _openai_singleton = OpenAIService()
    return _openai_singleton


def ask_openai(prompt: str, system_prompt: str = "You are a helpful assistant for OrdEasy.") -> str:
    """
    Convenience function used by agents:
        from app.services.openai_service import ask_openai
        text = ask_openai(prompt)
    """
    return get_openai_service().generate(prompt, system_prompt=system_prompt)
