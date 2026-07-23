import logging
import google.generativeai as genai
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialise clients once at import time
from groq import AsyncGroq
_groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
genai.configure(api_key=settings.GEMINI_API_KEY)


class GroqClient:
    MODEL = "llama-3.1-70b-versatile"

    async def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        response = await _groq_client.chat.completions.create(
            model=self.MODEL,
            temperature=temperature,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()


class GeminiClient:
    MODEL = "gemini-1.5-flash"

    async def complete(self, system: str, user: str, temperature: float = 0.5) -> str:
        model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=system,
            generation_config={"temperature": temperature, "max_output_tokens": 1000},
        )
        response = await model.generate_content_async(user)
        return response.text.strip()


class FallbackLLMClient:
    """Tries Groq first. On any failure, automatically falls back to Gemini."""

    def __init__(self):
        self.groq = GroqClient()
        self.gemini = GeminiClient()

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.8,
        prefer_gemini: bool = False,
    ) -> tuple[str, bool]:
        if prefer_gemini:
            text = await self.gemini.complete(system, user, temperature)
            return text, False

        try:
            text = await self.groq.complete(system, user, temperature)
            return text, False
        except Exception as e:
            logger.warning(f"[FallbackLLM] Groq failed ({e}), switching to Gemini.")
            text = await self.gemini.complete(system, user, temperature)
            return text, True