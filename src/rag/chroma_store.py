"""
ChromaDB Persistent Document Store
Uses ChromaDB v1.5.0 native Python SDK with our SentenceTransformer embeddings.
Stores document chunks + embeddings persistently under data/chroma_db/.
"""
import logging
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import chromadb
from chromadb import PersistentClient
from haystack import Document

from src.config import CHROMA_DB_DIR, EMBEDDING_MODEL_NAME
from src.ingestion.indexer import get_text_embedder, get_document_embedder

logger = logging.getLogger(__name__)

COLLECTION_NAME = "rag_documents"


class ChromaDocumentStoreManager:
    """
    Persistent ChromaDB-backed document store.

    - Uses our existing SentenceTransformer model for embeddings (NOT ChromaDB's built-in).
    - Stores: document content, embedding vectors, and metadata.
    - Supports duplicate detection by file_hash.
    - Exposes a compatible interface for the agent's document_search_func.
    """

    def __init__(self, persist_dir: Optional[Path] = None):
        self._persist_dir = persist_dir or CHROMA_DB_DIR
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # PersistentClient auto-saves on every write — no manual .persist() needed
        self._client = PersistentClient(path=str(self._persist_dir))

        # Get or create our collection (embedding_function=None → we supply our own)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaDB store ready at {self._persist_dir} "
            f"— {self._collection.count()} chunks loaded"
        )

    # ── Write ─────────────────────────────────────────────────────────────────
    def write_documents(self, documents: List[Document]) -> int:
        """
        Writes Haystack Document objects (must already have .embedding set) into ChromaDB.
        Uses the document's existing embedding — does NOT re-embed here.
        Returns number of chunks written.
        """
        if not documents:
            return 0

        ids, embeddings, contents, metadatas = [], [], [], []

        for doc in documents:
            if doc.embedding is None:
                logger.warning(f"Skipping doc with no embedding: {doc.id}")
                continue

            doc_id = str(doc.id) if doc.id else str(uuid.uuid4())
            emb = doc.embedding
            if isinstance(emb, np.ndarray):
                emb = emb.tolist()

            ids.append(doc_id)
            embeddings.append(emb)
            contents.append(doc.content or "")

            # Serialize metadata — ChromaDB only accepts str/int/float/bool
            meta = {}
            for k, v in (doc.meta or {}).items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            metadatas.append(meta)

        if not ids:
            return 0

        # upsert prevents duplicate IDs if same doc is re-indexed
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )
        logger.info(f"Upserted {len(ids)} chunks into ChromaDB")
        return len(ids)

    # ── Query ─────────────────────────────────────────────────────────────────
    def query(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Embeds a query string and retrieves the top_k most similar documents.
        Returns a list of Haystack Document objects with metadata.
        """
        if self._collection.count() == 0:
            return []

        try:
            embedder = get_text_embedder(model_name=EMBEDDING_MODEL_NAME)
            query_embedding = embedder.run(text=query_text)["embedding"]
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            for i, (content, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                score = 1.0 - dist  # cosine distance → similarity
                docs.append(Document(
                    content=content,
                    meta=meta,
                    score=score,
                ))
            return docs

        except Exception as e:
            logger.error(f"ChromaDB query error: {e}", exc_info=True)
            return []

    # ── Utilities ─────────────────────────────────────────────────────────────
    def count_documents(self) -> int:
        """Returns total number of chunks in the collection."""
        return self._collection.count()

    def has_file(self, filename: str, file_hash: Optional[str] = None) -> bool:
        """
        Checks if a file's chunks are already in ChromaDB.
        Uses file_hash metadata if provided (more reliable), else filename.
        """
        try:
            if file_hash:
                res = self._collection.get(
                    where={"file_hash": file_hash},
                    limit=1,
                    include=[],
                )
            else:
                res = self._collection.get(
                    where={"filename": filename},
                    limit=1,
                    include=[],
                )
            return len(res["ids"]) > 0
        except Exception:
            return False

    def delete_file_chunks(self, filename: str) -> None:
        """Removes all chunks belonging to a specific file."""
        try:
            self._collection.delete(where={"filename": filename})
            logger.info(f"Deleted all chunks for file: {filename}")
        except Exception as e:
            logger.error(f"Error deleting chunks for {filename}: {e}")

    def get_indexed_filenames(self) -> List[str]:
        """Returns a unique list of filenames stored in ChromaDB."""
        try:
            result = self._collection.get(include=["metadatas"])
            filenames = set()
            for meta in result.get("metadatas", []):
                if meta and "filename" in meta:
                    filenames.add(meta["filename"])
            return sorted(filenames)
        except Exception:
            return []

    # ── Compatibility shim for agent tools ────────────────────────────────────
    def search_documents(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Convenience method compatible with agent tools.
        Returns list of dicts with content, filename, page, score.
        """
        docs = self.query(query_text=query, top_k=top_k)
        results = []
        for doc in docs:
            results.append({
                "content": doc.content,
                "filename": doc.meta.get("filename", "Unknown"),
                "page": doc.meta.get("page_number", 1),
                "source": "document",
                "score": doc.score or 0.0,
            })
        return results


# ── Singleton ─────────────────────────────────────────────────────────────────
_chroma_instance: Optional[ChromaDocumentStoreManager] = None


def get_chroma_store() -> ChromaDocumentStoreManager:
    """Returns the singleton ChromaDocumentStoreManager (created once per process)."""
    global _chroma_instance
    if _chroma_instance is None:
        _chroma_instance = ChromaDocumentStoreManager()
    return _chroma_instance
