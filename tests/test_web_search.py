"""
Unit tests for Web Search Service
"""
import pytest
from unittest.mock import MagicMock, patch
from haystack import Document

from src.web.search import WebSearchService, perform_web_search


def test_web_search_empty_query():
    """Test web search with empty query returns empty list."""
    service = WebSearchService()
    results = service.search("")
    assert results == []


def test_duckduckgo_search_mocked():
    """Test DuckDuckGo search returning formatted Haystack Documents."""
    mock_ddg_results = [
        {
            "title": "Python Programming",
            "href": "https://python.org",
            "body": "Python is a programming language.",
        },
        {
            "title": "Haystack Framework",
            "href": "https://haystack.deepset.ai",
            "body": "Haystack is an open-source LLM framework.",
        },
    ]

    with patch("duckduckgo_search.DDGS") as MockDDGS:
        mock_instance = MockDDGS.return_value
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.text.return_value = mock_ddg_results

        service = WebSearchService(tavily_api_key="")
        results = service.search("python programming", max_results=2)

        assert len(results) == 2
        assert isinstance(results[0], Document)
        assert results[0].content == "Python is a programming language."
        assert results[0].meta["title"] == "Python Programming"
        assert results[0].meta["url"] == "https://python.org"
        assert results[0].meta["source"] == "web"


def test_tavily_search_mocked():
    """Test Tavily search returning formatted Haystack Documents."""
    mock_tavily_response = {
        "results": [
            {
                "title": "Tavily Search API",
                "url": "https://tavily.com",
                "content": "Tavily is an AI search engine.",
                "score": 0.95,
            }
        ]
    }

    with patch("tavily.TavilyClient") as MockTavily:
        mock_client = MockTavily.return_value
        mock_client.search.return_value = mock_tavily_response

        service = WebSearchService(tavily_api_key="test-api-key")
        results = service.search("AI search", max_results=1)

        assert len(results) == 1
        assert results[0].content == "Tavily is an AI search engine."
        assert results[0].meta["title"] == "Tavily Search API"
        assert results[0].meta["url"] == "https://tavily.com"
        assert results[0].meta["provider"] == "tavily"


def test_perform_web_search_helper():
    """Test convenience wrapper perform_web_search."""
    with patch.object(WebSearchService, "search") as mock_search:
        mock_search.return_value = [Document(content="Test result", meta={"source": "web"})]
        results = perform_web_search("test query")
        assert len(results) == 1
        assert results[0].content == "Test result"
