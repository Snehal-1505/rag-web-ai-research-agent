"""
Web Search Service Module
Provides web search capabilities using Tavily API (when configured) with DuckDuckGo search fallback.
Converts search results into Haystack Document objects for agent consumption.
"""
import os
from typing import List, Dict, Any, Optional

from haystack import Document

from src.config import TAVILY_API_KEY


class WebSearchService:
    """
    Web search service supporting Tavily API with DuckDuckGo fallback.
    """

    def __init__(self, tavily_api_key: Optional[str] = None):
        self.tavily_api_key = tavily_api_key if tavily_api_key is not None else (TAVILY_API_KEY or os.getenv("TAVILY_API_KEY", ""))

    def search(self, query: str, max_results: int = 5) -> List[Document]:
        """
        Executes web search and returns a list of Haystack Document objects.

        Args:
            query: The search query string.
            max_results: Max number of search results to return.

        Returns:
            List of Haystack Document objects with content and metadata (title, url, source).
        """
        if not query or not query.strip():
            return []

        # Try Tavily search if API key is provided
        if self.tavily_api_key and self.tavily_api_key.strip():
            try:
                return self._search_tavily(query, max_results=max_results)
            except Exception as e:
                # Log or fallback to DuckDuckGo if Tavily fails
                pass

        # Fallback to DuckDuckGo search
        return self._search_duckduckgo(query, max_results=max_results)

    def _search_tavily(self, query: str, max_results: int = 5) -> List[Document]:
        """Internal Tavily search execution."""
        from tavily import TavilyClient

        client = TavilyClient(api_key=self.tavily_api_key)
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])

        documents = []
        for res in results:
            content = res.get("content", "") or res.get("snippet", "")
            doc = Document(
                content=content,
                meta={
                    "title": res.get("title", "Web Result"),
                    "url": res.get("url", ""),
                    "source": "web",
                    "provider": "tavily",
                    "score": res.get("score", 0.0),
                }
            )
            documents.append(doc)

        return documents

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Document]:
        """Internal DuckDuckGo search execution."""
        from duckduckgo_search import DDGS

        documents = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                for res in results:
                    content = res.get("body", "") or res.get("snippet", "")
                    doc = Document(
                        content=content,
                        meta={
                            "title": res.get("title", "Web Result"),
                            "url": res.get("href", "") or res.get("url", ""),
                            "source": "web",
                            "provider": "duckduckgo",
                        }
                    )
                    documents.append(doc)
        except Exception:
            # Return empty list on failure gracefully
            pass

        return documents


def perform_web_search(query: str, max_results: int = 5, api_key: Optional[str] = None) -> List[Document]:
    """
    Convenience function to perform web search.

    Args:
        query: Search string.
        max_results: Max search results.
        api_key: Optional Tavily API key override.

    Returns:
        List of Haystack Document objects.
    """
    service = WebSearchService(tavily_api_key=api_key)
    return service.search(query=query, max_results=max_results)
