"""
SQLite Chat Database Module
Manages persistent storage of conversations, messages, and uploaded documents.
Uses Python built-in sqlite3 — no extra dependencies required.
"""
import sqlite3
import hashlib
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChatDatabase:
    """
    Manages all SQLite operations for chat history and document tracking.
    Thread-safe: creates a new connection per operation (safe for Streamlit reruns).
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ── Connection helper ─────────────────────────────────────────────────────
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    # ── Schema ────────────────────────────────────────────────────────────────
    def _init_schema(self) -> None:
        """Creates tables if they don't already exist (idempotent)."""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL DEFAULT 'New Chat',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id              TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role            TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content         TEXT NOT NULL,
                    timestamp       TEXT NOT NULL,
                    metadata_json   TEXT,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS uploaded_documents (
                    id              TEXT PRIMARY KEY,
                    filename        TEXT NOT NULL,
                    stored_path     TEXT NOT NULL,
                    file_hash       TEXT NOT NULL UNIQUE,
                    upload_time     TEXT NOT NULL,
                    status          TEXT NOT NULL DEFAULT 'pending'
                                    CHECK(status IN ('pending','processing','ready','error')),
                    error_message   TEXT,
                    conversation_id TEXT,
                    FOREIGN KEY (conversation_id)
                        REFERENCES conversations(id) ON DELETE SET NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conv
                    ON messages(conversation_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_docs_hash
                    ON uploaded_documents(file_hash);
            """)

    # ── Conversations ─────────────────────────────────────────────────────────
    def create_conversation(self, title: str = "New Chat") -> str:
        """Creates a new conversation and returns its ID."""
        conv_id = str(uuid.uuid4())
        now = _now()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?,?,?,?)",
                (conv_id, title, now, now),
            )
        return conv_id

    def list_conversations(self) -> List[Dict[str, Any]]:
        """Returns all conversations ordered by most-recently updated."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def rename_conversation(self, conv_id: str, new_title: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                (new_title, _now(), conv_id),
            )

    def delete_conversation(self, conv_id: str) -> None:
        """Deletes conversation and its messages (CASCADE). Documents stay."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))

    def touch_conversation(self, conv_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE conversations SET updated_at=? WHERE id=?",
                (_now(), conv_id),
            )

    def set_title_from_first_message(self, conv_id: str, content: str) -> None:
        """Sets conversation title from first user message if still 'New Chat'."""
        title = content.strip()[:60]
        if len(content.strip()) > 60:
            title += "…"
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT title FROM conversations WHERE id=?", (conv_id,)
            ).fetchone()
            if row and row["title"] == "New Chat":
                conn.execute(
                    "UPDATE conversations SET title=?, updated_at=? WHERE id=?",
                    (title, _now(), conv_id),
                )

    # ── Messages ──────────────────────────────────────────────────────────────
    def save_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Saves a single message. Returns the message ID."""
        msg_id = str(uuid.uuid4())
        now = _now()
        meta_json = json.dumps(metadata) if metadata else None
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO messages
                   (id, conversation_id, role, content, timestamp, metadata_json)
                   VALUES (?,?,?,?,?,?)""",
                (msg_id, conv_id, role, content, now, meta_json),
            )
        self.touch_conversation(conv_id)
        return msg_id

    def load_messages(self, conv_id: str) -> List[Dict[str, Any]]:
        """Returns all messages for a conversation in chronological order."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT id, role, content, timestamp, metadata_json
                   FROM messages
                   WHERE conversation_id=?
                   ORDER BY timestamp ASC""",
                (conv_id,),
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.pop("metadata_json")) if d.get("metadata_json") else {}
            result.append(d)
        return result

    def count_messages(self, conv_id: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM messages WHERE conversation_id=?", (conv_id,)
            ).fetchone()
        return row["c"] if row else 0

    # ── Uploaded Documents ─────────────────────────────────────────────────────
    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Computes SHA-256 hash of file bytes for duplicate detection."""
        return hashlib.sha256(file_bytes).hexdigest()

    def find_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Returns existing document record if file already uploaded (by hash)."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM uploaded_documents WHERE file_hash=?", (file_hash,)
            ).fetchone()
        return dict(row) if row else None

    def register_document(
        self,
        filename: str,
        stored_path: str,
        file_hash: str,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Registers a new uploaded document. Returns document ID."""
        doc_id = str(uuid.uuid4())
        now = _now()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO uploaded_documents
                   (id, filename, stored_path, file_hash, upload_time, status, conversation_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (doc_id, filename, stored_path, file_hash, now, "pending", conversation_id),
            )
        return doc_id

    def update_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Updates document processing status."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE uploaded_documents SET status=?, error_message=? WHERE id=?",
                (status, error_message, doc_id),
            )

    def list_documents(self) -> List[Dict[str, Any]]:
        """Returns all registered documents, newest first."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM uploaded_documents ORDER BY upload_time DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def list_ready_documents(self) -> List[Dict[str, Any]]:
        """Returns only successfully indexed documents."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM uploaded_documents WHERE status='ready' ORDER BY upload_time DESC"
            ).fetchall()
        return [dict(r) for r in rows]


# ── Utility ───────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.utcnow().isoformat()
