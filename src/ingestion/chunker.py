"""
Document Chunker Module for Haystack AI RAG Application.

Splits Haystack Documents into smaller manageable chunks while preserving
all original document metadata.
"""
from typing import List
import nltk
from haystack import Document
from haystack.components.preprocessors import DocumentSplitter
from src.config import SPLIT_BY, SPLIT_LENGTH, SPLIT_OVERLAP

# Ensure required NLTK tokenizers are available
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


def chunk_documents(
    documents: List[Document],
    split_by: str = SPLIT_BY,
    split_length: int = SPLIT_LENGTH,
    split_overlap: int = SPLIT_OVERLAP,
) -> List[Document]:
    """
    Splits a list of Haystack Documents into smaller chunks using DocumentSplitter.

    Args:
        documents: List of input Haystack Documents.
        split_by: Unit to split by ('sentence', 'word', or 'passage').
        split_length: Number of units per chunk (e.g. 5 sentences).
        split_overlap: Overlap length between adjacent chunks (e.g. 1 sentence).

    Returns:
        List[Document]: List of chunked Haystack Document objects.
    """
    if not documents:
        return []

    splitter = DocumentSplitter(
        split_by=split_by,
        split_length=split_length,
        split_overlap=split_overlap,
    )

    result = splitter.run(documents=documents)
    return result.get("documents", [])
