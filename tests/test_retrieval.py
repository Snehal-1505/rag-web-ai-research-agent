"""
Unit tests for Vector Storage & Retrieval (Phase 4)
"""
import pytest
from haystack import Document

from src.rag.document_store import DocumentStoreManager
from src.ingestion.indexer import generate_document_embeddings, get_text_embedder
from src.rag.retriever import retrieve_documents, get_retriever


def test_document_store_manager():
    """Test document store operations (write, count, clear)."""
    manager = DocumentStoreManager()
    assert manager.count_documents() == 0

    docs = [
        Document(content="Test content 1", meta={"filename": "doc1.txt"}),
        Document(content="Test content 2", meta={"filename": "doc2.txt"}),
    ]
    
    written = manager.write_documents(docs)
    assert written == 2
    assert manager.count_documents() == 2

    manager.clear()
    assert manager.count_documents() == 0


def test_semantic_retrieval():
    """Test full semantic retrieval pipeline using vector embeddings."""
    manager = DocumentStoreManager()

    # 1. Create documents on different topics
    raw_docs = [
        Document(
            content="Haystack AI is an open source Python framework for building RAG applications and agents.",
            meta={"filename": "haystack.txt", "source": "docs"}
        ),
        Document(
            content="Baking chocolate cake requires flour, cocoa powder, sugar, butter, and eggs.",
            meta={"filename": "recipe.txt", "source": "kitchen"}
        ),
        Document(
            content="Solar panels convert sunlight into electrical energy using photovoltaic cells.",
            meta={"filename": "solar.txt", "source": "energy"}
        ),
    ]

    # 2. Generate embeddings for documents
    embedded_docs = generate_document_embeddings(raw_docs)
    manager.write_documents(embedded_docs)
    assert manager.count_documents() == 3

    # 3. Generate query embedding for a RAG-related question
    text_embedder = get_text_embedder()
    query_res = text_embedder.run(text="What is Haystack framework used for?")
    query_embedding = query_res["embedding"]

    # 4. Retrieve top 1 document
    retrieved = retrieve_documents(query_embedding, manager.store, top_k=1)

    assert len(retrieved) == 1
    top_doc = retrieved[0]
    assert "Haystack AI" in top_doc.content
    assert top_doc.meta["filename"] == "haystack.txt"
