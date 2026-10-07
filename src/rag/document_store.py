"""
Vector Document Store Management Module for Haystack AI RAG Application.

Isolates vector storage implementation (currently Haystack InMemoryDocumentStore).
Designed so that it can be easily replaced with QdrantDocumentStore or another
vector database in future without altering downstream RAG code.
"""
from typing import List, Optional
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore


class DocumentStoreManager:
    """
    Wrapper class managing document store lifecycle and operations.
    """

    def __init__(self):
        # Initialize Haystack InMemoryDocumentStore
        self._doc_store = InMemoryDocumentStore()

    @property
    def store(self) -> InMemoryDocumentStore:
        """Returns the underlying Haystack DocumentStore instance."""
        return self._doc_store

    def write_documents(self, documents: List[Document]) -> int:
        """
        Writes a list of Haystack Document objects (with embeddings) into the store.

        Args:
            documents: List of Haystack Document objects.

        Returns:
            int: Number of documents written.
        """
        if not documents:
            return 0

        self._doc_store.write_documents(documents)
        return len(documents)

    def count_documents(self) -> int:
        """Returns the total number of documents currently stored."""
        return self._doc_store.count_documents()

    def clear(self) -> None:
        """Clears all documents from the store by re-initializing it."""
        self._doc_store = InMemoryDocumentStore()


# Global default instance for application state
_default_manager: Optional[DocumentStoreManager] = None


def get_document_store_manager() -> DocumentStoreManager:
    """
    Returns the singleton instance of DocumentStoreManager.
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = DocumentStoreManager()
    return _default_manager
