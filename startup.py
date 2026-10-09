"""
startup.py — Pre-flight checks run before Streamlit starts on Render.
Downloads NLTK resources and pre-caches the embedding model so they're available instantly.
Run via: python startup.py && streamlit run app.py ...
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("startup")


def download_nltk():
    log.info("Downloading NLTK resources...")
    try:
        import nltk
        for resource in ["punkt", "punkt_tab"]:
            try:
                nltk.data.find(f"tokenizers/{resource}")
                log.info(f"  ✓ {resource} already present")
            except (LookupError, OSError):
                log.info(f"  ↓ downloading {resource}...")
                nltk.download(resource, quiet=True)
                log.info(f"  ✓ {resource} downloaded")
    except Exception as e:
        log.warning(f"NLTK setup warning (non-fatal): {e}")


def download_embedding_model():
    log.info("Pre-loading sentence-transformer embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
        log.info(f"  ↓ loading model {model_name}...")
        SentenceTransformer(model_name)
        log.info(f"  ✓ {model_name} pre-loaded and cached")
    except Exception as e:
        log.warning(f"Embedding model pre-load warning (non-fatal): {e}")


def verify_data_dirs():
    """Ensure all data directories exist under DATA_DIR."""
    from pathlib import Path
    data_dir_env = os.getenv("DATA_DIR", "")
    if data_dir_env:
        base = Path(data_dir_env)
        log.info(f"DATA_DIR={base} (from environment)")
    else:
        base = Path(__file__).resolve().parent / "data"
        log.info(f"DATA_DIR={base} (default local)")

    for subdir in ["uploads", "chroma_db", "documents"]:
        d = base / subdir
        d.mkdir(parents=True, exist_ok=True)
        log.info(f"  ✓ {d}")


if __name__ == "__main__":
    log.info("=== RAG App Pre-flight Startup ===")
    verify_data_dirs()
    download_nltk()
    download_embedding_model()
    log.info("=== Pre-flight complete ===")
