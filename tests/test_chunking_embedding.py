"""
Unit tests for Document Chunking & Embeddings (Phase 3)
"""
import pytest
from haystack import Document

from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import generate_document_embeddings, get_text_embedder


def test_chunk_documents():
    """Test splitting a multi-sentence document into smaller sentence chunks."""
    long_text = (
        "Haystack 2.0 is an open-source framework for building production-ready AI applications. "
        "It supports vector search and document retrieval out of the box. "
        "You can integrate local models like sentence-transformers seamlessly. "
        "Agents can use tools to route user questions dynamically. "
        "Retrieval-augmented generation improves answer precision significantly. "
        "Streamlit provides a clean user interface for web applications."
    )
    doc = Document(
        content=long_text,
        meta={"filename": "test_doc.txt", "file_type": "txt", "source": "test_source"}
    )

    chunks = chunk_documents([doc], split_by="sentence", split_length=2, split_overlap=1)
    
    assert len(chunks) > 1
    # Check that metadata is preserved in chunks
    for chunk in chunks:
        assert chunk.meta["filename"] == "test_doc.txt"
        assert chunk.meta["file_type"] == "txt"
        assert len(chunk.content) > 0


def test_generate_document_embeddings():
    """Test generating embeddings for Haystack documents using MiniLM-L6-v2."""
    doc = Document(
        content="Retrieval augmented generation connects LLMs with external knowledge stores.",
        meta={"filename": "rag.txt"}
    )

    embedded_docs = generate_document_embeddings([doc])

    assert len(embedded_docs) == 1
    embedded_doc = embedded_docs[0]
    assert embedded_doc.embedding is not None
    # sentence-transformers/all-MiniLM-L6-v2 vector dimension is 384
    assert len(embedded_doc.embedding) == 384


def test_text_embedder():
    """Test query embedding generation."""
    embedder = get_text_embedder()
    result = embedder.run(text="What is Retrieval Augmented Generation?")
    embedding = result.get("embedding")

    assert embedding is not None
    assert len(embedding) == 384
