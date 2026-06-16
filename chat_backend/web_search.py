import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
logger = logging.getLogger("ChatBackend")


class WebSearchService:
    """
    Tavily-powered web search. Only searches when the query seems to require
    live/external information (e.g. recent news, unknown topics).
    """

    STROKE_KEYWORDS = [
        "stroke", "neuroscan", "facial asymmetry", "mediapipe", "symptom",
        "treatment", "recovery", "hospital", "emergency", "brain", "tpa",
        "thrombectomy", "rehabilitation", "risk factor", "blood pressure",
        "cholesterol", "diabetes", "atrial fibrillation"
    ]

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.enabled = bool(self.api_key)
        self.client = None

        if self.enabled:
            try:
                from tavily import TavilyClient
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily web search enabled.")
            except ImportError:
                logger.warning("tavily-python not installed. Run: pip install tavily-python")
                self.enabled = False
        else:
            logger.warning("TAVILY_API_KEY not set. Web search disabled.")

    def _should_search(self, query: str) -> bool:
        """Decide if query needs a web search (stroke-related topics always searched)."""
        q = query.lower()
        return any(kw in q for kw in self.STROKE_KEYWORDS)

    def search(self, query: str, max_results: int = 3) -> Optional[str]:
        """
        Searches Tavily and returns a formatted string of results,
        or None if search is disabled or not needed.
        """
        if not self.enabled or not self.client:
            return None

        try:
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True,
            )

            snippets = []

            # Tavily can return a direct answer
            if response.get("answer"):
                snippets.append(f"Summary: {response['answer']}")

            # Add individual result snippets
            for result in response.get("results", []):
                title = result.get("title", "")
                content = result.get("content", "")[:300]
                url = result.get("url", "")
                snippets.append(f"• {title}: {content} (Source: {url})")

            if snippets:
                return "\n".join(snippets)

        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")

        return None
