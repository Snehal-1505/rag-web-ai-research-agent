"""
Document and Text Embedder Module for Haystack AI RAG Application.

Uses local HuggingFace embedding models via SentenceTransformers.
Default model: sentence-transformers/all-MiniLM-L6-v2
"""
from typing import List, Optional
from haystack import Document
from haystack_integrations.components.embedders.sentence_transformers import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from src.config import EMBEDDING_MODEL_NAME


def get_document_embedder(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformersDocumentEmbedder:
    """
    Initializes and warms up a SentenceTransformersDocumentEmbedder component.
    """
    embedder = SentenceTransformersDocumentEmbedder(model=model_name)
    embedder.warm_up()
    return embedder


def get_text_embedder(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformersTextEmbedder:
    """
    Initializes and warms up a SentenceTransformersTextEmbedder component for query embedding.
    """
    embedder = SentenceTransformersTextEmbedder(model=model_name)
    embedder.warm_up()
    return embedder


def generate_document_embeddings(
    documents: List[Document],
    model_name: str = EMBEDDING_MODEL_NAME,
    file_hash: Optional[str] = None,
) -> List[Document]:
    """
    Generates vector embeddings for a list of Haystack Document objects.

    Args:
        documents: List of Haystack Document objects.
        model_name: Hugging Face model identifier.
        file_hash: Optional SHA-256 hash to tag documents for dedup tracking.

    Returns:
        List[Document]: Documents enriched with vector embeddings in doc.embedding.
    """
    if not documents:
        return []

    # Optionally tag each document with file_hash for ChromaDB dedup
    if file_hash:
        for doc in documents:
            if doc.meta is None:
                doc.meta = {}
            doc.meta["file_hash"] = file_hash

    embedder = get_document_embedder(model_name=model_name)
    result = embedder.run(documents=documents)
    return result.get("documents", [])
