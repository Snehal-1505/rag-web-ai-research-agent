"""
Agent Tools Module
Defines tools for document retrieval and web search to be used by the Haystack AI Agent.
Supports both InMemoryDocumentStore (legacy) and ChromaDocumentStoreManager (persistent).
"""
from typing import List, Optional, Dict, Any
from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.tools import Tool

from src.ingestion.indexer import get_text_embedder
from src.web.search import perform_web_search


def document_search_func(query: str, document_store, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the indexed local documents for relevant context using semantic vector retrieval.
    Automatically detects whether store is InMemory or ChromaDB and routes accordingly.

    Args:
        query: The search query string.
        document_store: InMemoryDocumentStore OR ChromaDocumentStoreManager instance.
        top_k: Number of relevant document chunks to retrieve.

    Returns:
        List of dictionaries with document content and metadata.
    """
    if document_store is None:
        return []

    try:
        # ── ChromaDocumentStoreManager path ──────────────────────────────────
        if hasattr(document_store, "search_documents"):
            if document_store.count_documents() == 0:
                return []
            return document_store.search_documents(query=query, top_k=top_k)

        # ── Legacy InMemoryDocumentStore path ─────────────────────────────────
        if document_store.count_documents() == 0:
            return []

        embedder = get_text_embedder()
        query_vector = embedder.run(text=query)["embedding"]
        retriever = InMemoryEmbeddingRetriever(document_store=document_store, top_k=top_k)
        retrieved_docs = retriever.run(query_embedding=query_vector)["documents"]

        results = []
        for doc in retrieved_docs:
            results.append({
                "content": doc.content,
                "filename": doc.meta.get("filename", "Unknown"),
                "page": doc.meta.get("page_number", 1),
                "source": "document",
                "score": doc.score if hasattr(doc, "score") else 0.0,
            })
        return results

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Document search error: {e}", exc_info=True)
        return []


def web_search_func(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the public web for real-time, current, or external information.

    Args:
        query: The search query string.
        max_results: Max number of search results to return.

    Returns:
        List of dictionaries with web search title, URL, snippet, and content.
    """
    try:
        docs = perform_web_search(query=query, max_results=max_results)
        results = []
        for doc in docs:
            results.append({
                "content": doc.content,
                "title": doc.meta.get("title", "Web Page"),
                "url": doc.meta.get("url", ""),
                "source": "web",
                "provider": doc.meta.get("provider", "web"),
            })
        return results
    except Exception as e:
        return [{"error": f"Web search error: {str(e)}"}]


def get_document_search_tool(document_store) -> Tool:
    """Creates a Haystack Tool for searching indexed documents."""

    def tool_fn(query: str) -> List[Dict[str, Any]]:
        return document_search_func(query=query, document_store=document_store)

    return Tool(
        name="document_search",
        description="Searches through the user's uploaded local documents (PDFs, TXT, DOCX) to find specific facts, definitions, and document context.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up in the uploaded documents."
                }
            },
            "required": ["query"]
        },
        function=tool_fn,
    )


def get_web_search_tool() -> Tool:
    """Creates a Haystack Tool for searching the web."""
    return Tool(
        name="web_search",
        description="Searches the live web for recent news, external facts, real-time data, or topics not covered in local uploaded documents.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to search on the web."
                }
            },
            "required": ["query"]
        },
        function=tool_fn_web,
    )


def tool_fn_web(query: str) -> List[Dict[str, Any]]:
    return web_search_func(query=query)
