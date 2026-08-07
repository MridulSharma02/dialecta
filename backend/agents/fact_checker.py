import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus
from core.llm_clients import FallbackLLMClient

logger = logging.getLogger(__name__)

MAX_RESULTS = 3
MAX_CHARS = 400
REQUEST_TIMEOUT = 6


def _search_duckduckgo(query: str) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_RESULTS))
        return results
    except Exception as e:
        logger.warning(f"[FactChecker] DuckDuckGo search failed: {e}")
        return []


def _fetch_page_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:MAX_CHARS]
    except Exception as e:
        logger.warning(f"[FactChecker] Could not fetch {url}: {e}")
        return ""


def _build_fact_context_from_search(sub_topic: str) -> str:
    results = _search_duckduckgo(sub_topic)
    if not results:
        return ""

    snippets = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        url = r.get("href", "")
        snippet = body[:MAX_CHARS] if body else ""
        if len(snippet) < 100 and url:
            page_text = _fetch_page_text(url)
            if page_text:
                snippet = page_text
        if snippet:
            snippets.append(f"- {title}: {snippet}")

    return "\n".join(snippets) if snippets else ""


SYSTEM_PROMPT = """You are a fact-research assistant. Given a debate sub-topic, provide 3-5 concrete, specific, well-known facts, statistics, or real-world examples relevant to the topic. These facts will be used by debaters to ground their arguments. Be concise and factual. Format as bullet points."""


class FactChecker(BaseAgent):
    def __init__(self):
        super().__init__(name="FactChecker")
        self.llm_client = FallbackLLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        try:
            # First try DuckDuckGo search
            loop = asyncio.get_event_loop()
            fact_context = await loop.run_in_executor(
                None, _build_fact_context_from_search, context.sub_topic
            )

            # If search returned nothing useful, fall back to LLM-generated facts
            if not fact_context:
                logger.info(f"[FactChecker] Search failed, using LLM fallback for: {context.sub_topic[:50]}")
                user_prompt = f"Provide key facts, statistics, and real-world examples for this debate topic:\n\n{context.sub_topic}"
                fact_context, _ = await self.llm_client.complete(
                    SYSTEM_PROMPT, user_prompt, temperature=0.3, prefer_gemini=False
                )

            logger.info(f"[FactChecker] Facts gathered for: {context.sub_topic[:50]}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.OK,
                data={"fact_context": fact_context},
            )

        except Exception as e:
            logger.error(f"[FactChecker] Failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.DEGRADED,
                data={"fact_context": "Fact checking unavailable."},
                error=str(e),
            )