"""
Document Chunker Module for Haystack AI RAG Application.

Splits Haystack Documents into smaller manageable chunks while preserving
all original document metadata.
"""
import logging
import os
import shutil
from typing import List

from haystack import Document
from haystack.components.preprocessors import DocumentSplitter
from src.config import SPLIT_BY, SPLIT_LENGTH, SPLIT_OVERLAP

logger = logging.getLogger(__name__)


def ensure_nltk_resources():
    """
    Ensures NLTK tokenizers ('punkt' and 'punkt_tab') exist and compatibility
    directories are mapped so Haystack's DocumentSplitter sentence tokenizer
    operates reliably across NLTK versions on Windows.
    """
    try:
        import nltk

        # 1. Download punkt and punkt_tab if missing
        for resource in ["punkt_tab", "punkt"]:
            try:
                nltk.data.find(f"tokenizers/{resource}")
            except (LookupError, OSError):
                try:
                    nltk.download(resource, quiet=True)
                except Exception as dl_err:
                    logger.warning(f"Could not download NLTK resource '{resource}': {dl_err}")

        # 2. Ensure NLTK directory structure compatibility for Haystack sentence tokenizer
        for data_path in nltk.data.path:
            tok_dir = os.path.join(data_path, "tokenizers")
            p_dir = os.path.join(tok_dir, "punkt")
            pt_dir = os.path.join(tok_dir, "punkt_tab")

            if os.path.exists(p_dir):
                py3_tab_dir = os.path.join(p_dir, "PY3_tab")
                if os.path.isfile(py3_tab_dir):
                    try:
                        os.remove(py3_tab_dir)
                    except Exception:
                        pass
                os.makedirs(py3_tab_dir, exist_ok=True)

                eng_src = os.path.join(p_dir, "english.pickle")
                if os.path.exists(eng_src):
                    eng_dst_py3 = os.path.join(py3_tab_dir, "english.pickle")
                    if not os.path.exists(eng_dst_py3):
                        try:
                            shutil.copy(eng_src, eng_dst_py3)
                        except Exception:
                            pass

                    if os.path.exists(pt_dir):
                        eng_dst_pt = os.path.join(pt_dir, "english.pickle")
                        if not os.path.exists(eng_dst_pt):
                            try:
                                shutil.copy(eng_src, eng_dst_pt)
                            except Exception:
                                pass
    except Exception as e:
        logger.warning(f"Error ensuring NLTK resources: {e}")


def chunk_documents(
    documents: List[Document],
    split_by: str = SPLIT_BY,
    split_length: int = SPLIT_LENGTH,
    split_overlap: int = SPLIT_OVERLAP,
) -> List[Document]:
    """
    Splits a list of Haystack Documents into smaller chunks using Haystack's
    native DocumentSplitter component.

    Args:
        documents: List of input Haystack Documents.
        split_by: Unit to split by ('word', 'sentence', 'passage', 'line', 'page').
        split_length: Number of units per chunk.
        split_overlap: Overlap length between adjacent chunks.

    Returns:
        List[Document]: List of chunked Haystack Document objects with metadata.
    """
    if not documents:
        return []

    ensure_nltk_resources()

    try:
        splitter = DocumentSplitter(
            split_by=split_by,
            split_length=split_length,
            split_overlap=split_overlap,
        )
        result = splitter.run(documents=documents)
        return result.get("documents", [])
    except Exception as err:
        logger.warning(
            f"DocumentSplitter with split_by='{split_by}' encountered an issue ({err}). "
            "Falling back to native word-based DocumentSplitter."
        )
        fallback_splitter = DocumentSplitter(
            split_by="word",
            split_length=split_length if split_by != "sentence" else 150,
            split_overlap=split_overlap if split_by != "sentence" else 20,
        )
        result = fallback_splitter.run(documents=documents)
        return result.get("documents", [])
