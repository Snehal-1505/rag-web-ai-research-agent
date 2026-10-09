"""
startup.py — Fast pre-flight checks run before Streamlit starts on Render.
Ensures data directories and NLTK tokenizers exist in <2 seconds.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("startup")


def download_nltk():
    try:
        import nltk
        for resource in ["punkt", "punkt_tab"]:
            try:
                nltk.data.find(f"tokenizers/{resource}")
            except (LookupError, OSError):
                nltk.download(resource, quiet=True)
    except Exception as e:
        log.warning(f"NLTK setup warning: {e}")


def verify_data_dirs():
    """Ensure all data directories exist under DATA_DIR."""
    from pathlib import Path
    data_dir_env = os.getenv("DATA_DIR", "")
    if data_dir_env:
        base = Path(data_dir_env)
    else:
        base = Path(__file__).resolve().parent / "data"

    for subdir in ["uploads", "chroma_db", "documents"]:
        (base / subdir).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    log.info("=== RAG App Pre-flight Startup ===")
    verify_data_dirs()
    download_nltk()
    log.info("=== Pre-flight ready — starting Streamlit ===")
