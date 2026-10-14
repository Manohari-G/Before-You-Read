import logging
import os
import time
from typing import Optional

from google import genai

logger = logging.getLogger("before_you_read.llm")


class GeminiServiceError(Exception):
    def __init__(self, user_message: str, status_code: int | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.status_code = status_code


class GeminiLLM:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")
        self.client = genai.Client(api_key=api_key)
        self.primary_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "").strip() or None
        self.max_retries = 2

    @staticmethod
    def _status_from_error(exc: Exception) -> Optional[int]:
        for attr in ("status_code", "code", "http_status"):
            value = getattr(exc, attr, None)
            if isinstance(value, int):
                return value
        text = str(exc)
        for code in (503, 429, 403, 401, 400):
            if str(code) in text:
                return code
        return None

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        status = GeminiLLM._status_from_error(exc)
        text = str(exc).lower()
        return status in {429, 500, 502, 503, 504} or any(
            word in text for word in ("timeout", "temporarily", "unavailable", "connection")
        )

    @staticmethod
    def _user_message(status: int | None, exc: Exception) -> str:
        if status == 429:
            return "The AI service is temporarily rate-limited. Please wait a moment and try again."
        if status == 503:
            return "The AI service is temporarily busy. Please try again in a moment."
        if status in {401, 403}:
            return "The Gemini API key was rejected. Check GEMINI_API_KEY in backend/.env."
        if status == 400:
            return "The configured Gemini model or request is invalid. Check GEMINI_MODEL in backend/.env."
        return "The AI service could not complete the request. Please try again."

    def generate(self, prompt: str) -> str:
        models = [self.primary_model]
        if self.fallback_model and self.fallback_model != self.primary_model:
            models.append(self.fallback_model)

        last_exc: Exception | None = None
        for model_index, model in enumerate(models):
            for attempt in range(self.max_retries + 1):
                try:
                    logger.info("Calling Gemini model=%s attempt=%s", model, attempt + 1)
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    text = (response.text or "").strip()
                    if not text:
                        raise RuntimeError("Gemini returned an empty response.")
                    return text
                except Exception as exc:
                    last_exc = exc
                    status = self._status_from_error(exc)
                    logger.exception(
                        "Gemini call failed: model=%s attempt=%s status=%s error=%s",
                        model, attempt + 1, status, exc,
                    )
                    if not self._retryable(exc) or attempt >= self.max_retries:
                        break
                    time.sleep(2 ** attempt)

            if model_index < len(models) - 1:
                logger.warning("Primary Gemini model failed; trying fallback model=%s", models[model_index + 1])

        status = self._status_from_error(last_exc) if last_exc else None
        raise GeminiServiceError(self._user_message(status, last_exc or RuntimeError()), status)
