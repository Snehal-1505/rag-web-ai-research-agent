"""
Document Retrieval Module for Haystack AI RAG Application.

Uses Haystack InMemoryEmbeddingRetriever to retrieve top_k documents matching
a query's vector embedding.
"""
from typing import List
from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore


def get_retriever(
    document_store: InMemoryDocumentStore,
    top_k: int = 5,
) -> InMemoryEmbeddingRetriever:
    """
    Initializes and returns an InMemoryEmbeddingRetriever component.

    Args:
        document_store: Active Haystack InMemoryDocumentStore instance.
        top_k: Number of relevant document chunks to retrieve (default: 5).

    Returns:
        InMemoryEmbeddingRetriever instance.
    """
    return InMemoryEmbeddingRetriever(document_store=document_store, top_k=top_k)


def retrieve_documents(
    query_embedding: List[float],
    document_store: InMemoryDocumentStore,
    top_k: int = 5,
) -> List[Document]:
    """
    Retrieves top_k relevant documents matching the query vector.

    Args:
        query_embedding: Vector embedding of the query.
        document_store: Active document store containing indexed documents.
        top_k: Maximum number of top documents to return.

    Returns:
        List[Document]: List of relevant Haystack Document objects with similarity scores.
    """
    retriever = get_retriever(document_store=document_store, top_k=top_k)
    result = retriever.run(query_embedding=query_embedding)
    return result.get("documents", [])
