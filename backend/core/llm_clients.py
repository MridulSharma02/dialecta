import logging
import httpx
import google.generativeai as genai
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

from groq import AsyncGroq
_groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
genai.configure(api_key=settings.GEMINI_API_KEY)


class GroqClient:
    MODEL = "llama-3.3-70b-versatile"

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
    MODEL = "gemini-2.0-flash"

    async def complete(self, system: str, user: str, temperature: float = 0.5) -> str:
        model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=system,
            generation_config={"temperature": temperature, "max_output_tokens": 1000},
        )
        response = await model.generate_content_async(user)
        return response.text.strip()


class CloudflareClient:
    MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

    async def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        account_id = settings.CLOUDFLARE_ACCOUNT_ID
        api_token = settings.CLOUDFLARE_API_TOKEN

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{self.MODEL}"

        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 1000,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["result"]["response"].strip()


class FallbackLLMClient:
    """Tries Groq first. On failure falls back to Gemini. On failure falls back to Cloudflare."""

    def __init__(self):
        self.groq = GroqClient()
        self.gemini = GeminiClient()
        self.cloudflare = CloudflareClient()

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.8,
        prefer_gemini: bool = False,
    ) -> tuple[str, bool]:
        if prefer_gemini:
            try:
                text = await self.gemini.complete(system, user, temperature)
                return text, False
            except Exception as e:
                logger.warning(f"[FallbackLLM] Gemini failed ({e}), falling back to Groq.")
                try:
                    text = await self.groq.complete(system, user, temperature)
                    return text, True
                except Exception as e2:
                    logger.warning(f"[FallbackLLM] Groq failed ({e2}), falling back to Cloudflare.")
                    text = await self.cloudflare.complete(system, user, temperature)
                    return text, True

        try:
            text = await self.groq.complete(system, user, temperature)
            return text, False
        except Exception as e:
            logger.warning(f"[FallbackLLM] Groq failed ({e}), switching to Gemini.")
            try:
                text = await self.gemini.complete(system, user, temperature)
                return text, True
            except Exception as e2:
                logger.warning(f"[FallbackLLM] Gemini failed ({e2}), falling back to Cloudflare.")
                text = await self.cloudflare.complete(system, user, temperature)
                return text, True