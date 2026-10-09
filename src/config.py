import os
from pathlib import Path
from dotenv import load_dotenv

# ── Base directory ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (local dev only — Render uses env vars directly)
load_dotenv(BASE_DIR / ".env", override=False)

# ── API Keys ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Embedding Model ────────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# ── Chunking Defaults ─────────────────────────────────────────────────────────
SPLIT_BY = "word"
SPLIT_LENGTH = 150
SPLIT_OVERLAP = 20

# ── Data Directory ─────────────────────────────────────────────────────────────
# On Render: set DATA_DIR=/var/data  (persistent disk mount point)
# Locally:   defaults to <project_root>/data
_data_env = os.getenv("DATA_DIR", "")
if _data_env:
    DATA_DIR = Path(_data_env)
else:
    DATA_DIR = BASE_DIR / "data"

DOCUMENTS_DIR = DATA_DIR / "documents"
UPLOADS_DIR   = DATA_DIR / "uploads"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
SQLITE_DB_PATH = DATA_DIR / "chat_history.db"

# ── Create required directories (safe — never deletes existing data) ───────────
for _d in [DOCUMENTS_DIR, UPLOADS_DIR, CHROMA_DB_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
