"""
Unit tests for ResearchAgent and Agent Tools
"""
import pytest
from unittest.mock import MagicMock, patch
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack import Document

from src.agent.tools import document_search_func, web_search_func, get_document_search_tool, get_web_search_tool
from src.agent.research_agent import ResearchAgent


def test_determine_search_strategy_no_docs():
    """Agent defaults to web search when no documents are uploaded."""
    agent = ResearchAgent(api_key="fake-key")
    strategy = agent.determine_search_strategy("What is python?", has_documents=False)
    assert strategy == "web"


def test_determine_search_strategy_doc_intent():
    """Agent routes to documents search when query asks about uploaded doc."""
    agent = ResearchAgent(api_key="fake-key")
    strategy = agent.determine_search_strategy("What does my uploaded file say about budget?", has_documents=True)
    assert strategy == "documents"


def test_determine_search_strategy_web_intent():
    """Agent routes to web search when query asks about recent/current news."""
    agent = ResearchAgent(api_key="fake-key")
    strategy = agent.determine_search_strategy("What is the latest stock price of Apple today?", has_documents=True)
    assert strategy == "web"


def test_determine_search_strategy_hybrid():
    """Agent defaults to hybrid search when documents are present for general question."""
    agent = ResearchAgent(api_key="fake-key")
    strategy = agent.determine_search_strategy("Compare machine learning models", has_documents=True)
    assert strategy == "hybrid"


def test_document_search_func_empty_store():
    """Document search returns empty list on empty store."""
    store = InMemoryDocumentStore()
    results = document_search_func("query", store)
    assert results == []


def test_research_agent_run_mocked():
    """Test full agent execution with mocked generator and search tools."""
    agent = ResearchAgent(api_key="fake-key")

    with patch.object(agent.generator, "run") as mock_gen, \
         patch("src.agent.research_agent.document_search_func") as mock_doc_search, \
         patch("src.agent.research_agent.web_search_func") as mock_web_search:

        mock_gen.return_value = {"replies": ["Synthesized answer based on doc and web."]}
        mock_doc_search.return_value = [{"content": "Doc content", "filename": "test.pdf", "page": 1}]
        mock_web_search.return_value = [{"content": "Web content", "title": "Web Title", "url": "https://example.com"}]

        mock_store = MagicMock()
        mock_store.count_documents.return_value = 5

        res = agent.run(question="Explain topic", document_store=mock_store)

        assert res["strategy"] == "hybrid"
        assert res["answer"] == "Synthesized answer based on doc and web."
        assert len(res["doc_results"]) == 1
        assert len(res["web_results"]) == 1
