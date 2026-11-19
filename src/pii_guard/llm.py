"""LLM sarmalayıcısı — Gemini SDK'ya tek bağımlılık noktası.

v0.4.0'da google-generativeai → google-genai geçişi yalnızca bu dosyayı etkileyecektir.
"""

import logging
from functools import lru_cache

import google.generativeai as genai  # noqa: N812

from pii_guard.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are an assistant working behind a secure proxy. "
    "You will see placeholders like PERSON_1, PERSON_2 in the input text. "
    "DO NOT transform, translate, or change these placeholders into real names or values. "
    "Keep them EXACTLY as they are in your response, and treat them as if they are the actual names."
)


class LLMClient:
    """Gemini GenerativeModel etrafında ince sarmalayıcı."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key or not settings.gemini_api_key.get_secret_value().strip():
            raise ValueError(
                "GEMINI_API_KEY is not set or empty. "
                "Add it to your .env file or environment."
            )
        genai.configure(api_key=settings.gemini_api_key.get_secret_value())
        self._model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_INSTRUCTION,
        )
        logger.info("LLM istemcisi oluşturuldu (model=%s)", settings.gemini_model)

    def generate(self, prompt: str) -> str:
        """Verilen prompt'u modele gönderir ve yanıt metnini döner."""
        response = self._model.generate_content(prompt)
        return response.text


@lru_cache
def get_llm_client() -> LLMClient:
    """LLMClient tekil örneğini döner. İlk çağrıda API anahtarı doğrulanır."""
    return LLMClient()
