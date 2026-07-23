import logging
import asyncio
from bs4 import BeautifulSoup
import requests
from duckduckgo_search import DDGS
from agents.base import BaseAgent, AgentContext, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

MAX_RESULTS = 3        # Number of search results to fetch
MAX_CHARS = 300        # Characters to extract per page
REQUEST_TIMEOUT = 6    # Seconds before giving up on a page


def _search_duckduckgo(query: str) -> list[dict]:
    """Run a DuckDuckGo search and return top results."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_RESULTS))
        return results
    except Exception as e:
        logger.warning(f"[FactChecker] DuckDuckGo search failed: {e}")
        return []


def _fetch_page_text(url: str) -> str:
    """Fetch a webpage and extract clean text."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Return first MAX_CHARS characters only
        return text[:MAX_CHARS]
    except Exception as e:
        logger.warning(f"[FactChecker] Could not fetch {url}: {e}")
        return ""


def _build_fact_context(sub_topic: str) -> str:
    """Search + scrape + compile fact context string."""
    results = _search_duckduckgo(sub_topic)
    if not results:
        return "No fact context available."

    snippets = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        url = r.get("href", "")

        # Use snippet from search result first
        snippet = body[:MAX_CHARS] if body else ""

        # Try to enrich with page content if snippet is short
        if len(snippet) < 100 and url:
            page_text = _fetch_page_text(url)
            if page_text:
                snippet = page_text

        if snippet:
            snippets.append(f"- {title}: {snippet}")

    return "\n".join(snippets) if snippets else "No fact context available."


class FactChecker(BaseAgent):
    def __init__(self):
        super().__init__(name="FactChecker")

    async def run(self, context: AgentContext) -> AgentResult:
        try:
            # Run in thread pool so it doesn't block the async event loop
            loop = asyncio.get_event_loop()
            fact_context = await loop.run_in_executor(
                None, _build_fact_context, context.sub_topic
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