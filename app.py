"""
RAG + Web AI Research Agent — Persistent Chatbot UI
Clean chatbot interface with ChromaDB document storage + SQLite chat history.
"""
import os
import sys
import shutil
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st

# ── Logging (errors to terminal only) ─────────────────────────────────────────
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    GEMINI_API_KEY, TAVILY_API_KEY,
    UPLOADS_DIR, SQLITE_DB_PATH, CHROMA_DB_DIR,
)
from src.ingestion.document_loader import load_document
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import generate_document_embeddings
from src.rag.chroma_store import get_chroma_store, ChromaDocumentStoreManager
from src.agent.research_agent import ResearchAgent
from src.database.chat_database import ChatDatabase

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Singleton store + DB (created once per process, reused across reruns) ─────
@st.cache_resource
def get_persistent_store() -> ChromaDocumentStoreManager:
    return get_chroma_store()

@st.cache_resource
def get_chat_db() -> ChatDatabase:
    return ChatDatabase(SQLITE_DB_PATH)

chroma_store = get_persistent_store()
chat_db = get_chat_db()

# ── Session state ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "conv_id": None,           # Active conversation UUID
        "messages": [],            # In-memory message list for current conv
        "api_key": os.getenv("GEMINI_API_KEY", GEMINI_API_KEY or ""),
        "tavily_key": os.getenv("TAVILY_API_KEY", TAVILY_API_KEY or ""),
        "top_k_docs": 5,
        "max_web_results": 5,
        "upload_status": None,     # None | "processing" | "ready" | "duplicate" | "error"
        "upload_filename": "",
        "pending_question": None,  # Set by suggestion chip clicks
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ── Smart System Prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an intelligent AI Research Assistant.

Choose the best response format automatically based on the question:
- Short paragraph → simple "what is" questions
- Numbered steps → "how to" / process questions
- Bullet list → advantages, features, lists
- Markdown table → comparison questions (X vs Y)
- Structured sections (## Short Answer, ## Key Findings, ## Explanation) → complex research
- Plain simple language → "explain like I'm a beginner" questions
- Code blocks → programming questions

Rules:
- Match response length to question complexity. Short question = short answer.
- Do NOT show source URLs or citations unless the user explicitly asks "show me the sources".
- Do NOT expose backend details (Haystack, ChromaDB, vector store, embeddings, etc.).
- Be direct, clear, and helpful.
"""

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #F8FAFC;
    color: #0F172A;
  }

  /* ── Hide Streamlit default chrome ─────────────────────────────────── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 0 !important; padding-bottom: 0 !important; }

  /* ── Sidebar ─────────────────────────────────────────────────────── */
  [data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #E2E8F0;
    min-width: 240px !important;
    max-width: 260px !important;
  }
  [data-testid="stSidebar"] .block-container {
    padding: 0 !important;
  }

  .sidebar-header {
    padding: 16px 16px 8px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 1px solid #F1F5F9;
    margin-bottom: 6px;
  }

  .conv-item {
    padding: 8px 14px;
    border-radius: 8px;
    margin: 2px 8px;
    cursor: pointer;
    font-size: 0.83rem;
    color: #475569;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.12s;
  }
  .conv-item:hover { background: #F1F5F9; }
  .conv-item-active {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    font-weight: 600;
  }

  /* ── Main area ──────────────────────────────────────────────────── */
  .main-wrap { max-width: 760px; margin: 0 auto; padding: 0 16px; }

  /* ── Header ─────────────────────────────────────────────────────── */
  .chat-header {
    padding: 16px 0 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 12px;
  }
  .header-brand { display: flex; align-items: center; gap: 10px; }
  .header-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #2563EB, #14B8A6);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
  }
  .header-title { font-size: 1rem; font-weight: 700; color: #0F172A; margin: 0; }
  .header-sub { font-size: 0.73rem; color: #94A3B8; margin: 0; }

  /* ── Upload status pill ─────────────────────────────────────────── */
  .upload-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #F0FDF4; border: 1px solid #BBF7D0;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.78rem; color: #15803D; font-weight: 500;
    margin: 6px 0 4px;
  }
  .upload-pill-processing { background:#EFF6FF; border-color:#BFDBFE; color:#1D4ED8; }
  .upload-pill-duplicate  { background:#FFFBEB; border-color:#FDE68A; color:#92400E; }
  .upload-pill-error      { background:#FEF2F2; border-color:#FECACA; color:#DC2626; }

  /* ── Chat messages ──────────────────────────────────────────────── */
  [data-testid="stChatMessageContent"] {
    font-size: 0.92rem !important;
    line-height: 1.65 !important;
  }
  .stChatMessage { margin-bottom: 4px !important; }

  /* ── Empty state ────────────────────────────────────────────────── */
  .empty-state {
    text-align: center; padding: 56px 20px 32px; color: #94A3B8;
  }
  .empty-state-icon { font-size: 3rem; margin-bottom: 12px; }
  .empty-state h2 { font-size: 1.2rem; font-weight: 600; color: #475569; margin-bottom: 8px; }
  .empty-state p { font-size: 0.86rem; color: #94A3B8; margin-bottom: 24px; line-height: 1.6; }

  /* ── Chat input ─────────────────────────────────────────────────── */
  [data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    font-size: 0.92rem !important;
    background: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
  }
  [data-testid="stChatInput"] textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
  }
  [data-testid="stChatInput"] button {
    background: #2563EB !important; border-radius: 8px !important;
  }

  /* ── Markdown inside messages ───────────────────────────────────── */
  .stChatMessage table { font-size: 0.85rem; border-collapse: collapse; width: 100%; margin: 8px 0; }
  .stChatMessage th, .stChatMessage td { padding: 7px 11px; border: 1px solid #E2E8F0; text-align: left; }
  .stChatMessage th { background: #F8FAFC; font-weight: 600; }
  .stChatMessage code { background: #F1F5F9; padding: 2px 5px; border-radius: 4px; font-size: 0.84em; }
  .stChatMessage pre { background: #0F172A; color: #e2e8f0; padding: 14px; border-radius: 8px; overflow-x: auto; }

  /* ── Streamlit button → looks like a link ───────────────────────── */
  div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    color: #475569 !important;
    font-size: 0.82rem !important;
    padding: 6px 10px !important;
    text-align: left !important;
    width: 100% !important;
    border-radius: 8px !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: #F1F5F9 !important;
    color: #1D4ED8 !important;
  }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Conversation History
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-header">💬 Conversations</div>', unsafe_allow_html=True)

    # New Chat button
    if st.button("＋  New Chat", key="new_chat_btn", use_container_width=True):
        st.session_state.conv_id = None
        st.session_state.messages = []
        st.session_state.upload_status = None
        st.session_state.upload_filename = ""
        st.rerun()

    st.markdown("<hr style='margin:6px 0; border-color:#F1F5F9;'>", unsafe_allow_html=True)

    # Previous conversations
    conversations = chat_db.list_conversations()
    if conversations:
        for conv in conversations:
            cid = conv["id"]
            title = conv["title"]
            is_active = cid == st.session_state.conv_id
            label = f"{'●  ' if is_active else '○  '}{title}"
            if st.button(label, key=f"conv_{cid}", use_container_width=True):
                if cid != st.session_state.conv_id:
                    st.session_state.conv_id = cid
                    # Load messages from SQLite
                    db_msgs = chat_db.load_messages(cid)
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in db_msgs
                    ]
                    st.session_state.upload_status = None
                    st.rerun()
    else:
        st.markdown(
            '<div style="font-size:0.78rem;color:#CBD5E1;padding:8px 14px;">No conversations yet.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:6px 0; border-color:#F1F5F9;'>", unsafe_allow_html=True)

    # Indexed docs summary
    doc_count = chroma_store.count_documents()
    indexed_files = chroma_store.get_indexed_filenames()
    st.markdown(
        f'<div style="font-size:0.75rem;color:#94A3B8;padding:0 14px 4px;">'
        f'📚 {len(indexed_files)} document(s) indexed</div>',
        unsafe_allow_html=True,
    )
    if indexed_files:
        for fname in indexed_files[:5]:
            st.markdown(
                f'<div style="font-size:0.72rem;color:#CBD5E1;padding:1px 18px;">📄 {fname}</div>',
                unsafe_allow_html=True,
            )
        if len(indexed_files) > 5:
            st.markdown(
                f'<div style="font-size:0.72rem;color:#CBD5E1;padding:1px 18px;">+{len(indexed_files)-5} more…</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_clear = st.columns([6, 1])
with col_title:
    st.markdown("""
    <div style="padding:16px 0 8px;display:flex;align-items:center;gap:10px;">
      <div style="width:36px;height:36px;background:linear-gradient(135deg,#2563EB,#14B8A6);
                  border-radius:10px;display:flex;align-items:center;justify-content:center;
                  font-size:18px;flex-shrink:0;">🧠</div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#0F172A;line-height:1.2;">
          AI Research Assistant</div>
        <div style="font-size:0.73rem;color:#94A3B8;">
          Ask questions, explore documents, get intelligent answers.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_clear:
    st.markdown("<div style='padding-top:20px;'>", unsafe_allow_html=True)
    if st.button("✕ Clear", key="clear_chat_btn", help="Clear current conversation"):
        if st.session_state.conv_id:
            chat_db.delete_conversation(st.session_state.conv_id)
        st.session_state.conv_id = None
        st.session_state.messages = []
        st.session_state.upload_status = None
        st.session_state.upload_filename = ""
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin:0 0 8px;border:none;border-top:1px solid #E2E8F0;'>",
            unsafe_allow_html=True)

# ── Document Upload ────────────────────────────────────────────────────────────
with st.expander("📎 Attach a document (PDF, TXT, DOCX)", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload document",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=False,
        key="doc_uploader",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getbuffer().tobytes()
        file_hash = ChatDatabase.compute_file_hash(file_bytes)

        # ── Duplicate check ────────────────────────────────────────────────────
        existing = chat_db.find_document_by_hash(file_hash)
        if existing and existing["status"] == "ready":
            st.session_state.upload_status = "duplicate"
            st.session_state.upload_filename = uploaded_file.name
        elif uploaded_file.name != st.session_state.get("_last_uploaded_name"):
            # ── New file — process it ──────────────────────────────────────────
            st.session_state._last_uploaded_name = uploaded_file.name
            st.session_state.upload_status = "processing"
            st.session_state.upload_filename = uploaded_file.name

            with st.spinner(f"Processing {uploaded_file.name}…"):
                # Save file to disk
                dest_path = UPLOADS_DIR / uploaded_file.name
                dest_path.write_bytes(file_bytes)

                # Register in SQLite
                doc_id = chat_db.register_document(
                    filename=uploaded_file.name,
                    stored_path=str(dest_path),
                    file_hash=file_hash,
                    conversation_id=st.session_state.conv_id,
                )
                chat_db.update_document_status(doc_id, "processing")

                try:
                    raw_docs = load_document(dest_path)
                    if not raw_docs:
                        raise ValueError("No text content extracted from document.")

                    for doc in raw_docs:
                        doc.meta["filename"] = uploaded_file.name
                        doc.meta["source"] = uploaded_file.name
                        doc.meta["file_hash"] = file_hash
                        doc.meta["doc_registry_id"] = doc_id

                    chunks = chunk_documents(raw_docs)
                    embedded = generate_document_embeddings(
                        chunks, file_hash=file_hash
                    )
                    chroma_store.write_documents(embedded)
                    chat_db.update_document_status(doc_id, "ready")
                    st.session_state.upload_status = "ready"

                except Exception as e:
                    logger.error(f"Document indexing error: {e}", exc_info=True)
                    chat_db.update_document_status(doc_id, "error", str(e))
                    st.session_state.upload_status = "error"

# Upload status pill
status = st.session_state.upload_status
fname = st.session_state.upload_filename
if status == "ready":
    st.markdown(
        f'<div class="upload-pill">✓ <b>{fname}</b> is ready</div>',
        unsafe_allow_html=True,
    )
elif status == "duplicate":
    st.markdown(
        f'<div class="upload-pill upload-pill-duplicate">♻ <b>{fname}</b> already indexed — using existing version</div>',
        unsafe_allow_html=True,
    )
elif status == "processing":
    st.markdown(
        f'<div class="upload-pill upload-pill-processing">⏳ Processing <b>{fname}</b>…</div>',
        unsafe_allow_html=True,
    )
elif status == "error":
    st.markdown(
        f'<div class="upload-pill upload-pill-error">⚠ Could not process <b>{fname}</b>. Try another file.</div>',
        unsafe_allow_html=True,
    )

# Indexed files summary (compact)
indexed_files = chroma_store.get_indexed_filenames()
if indexed_files:
    files_txt = " · ".join(f"📄 {f}" for f in indexed_files)
    st.markdown(
        f'<div style="font-size:0.73rem;color:#94A3B8;padding:2px 0 6px;">{files_txt}</div>',
        unsafe_allow_html=True,
    )

# ── Empty state ────────────────────────────────────────────────────────────────
SUGGESTIONS = [
    "What is RAG?",
    "How does RAG work?",
    "RAG vs fine-tuning",
    "Explain embeddings simply",
]

if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
      <div class="empty-state-icon">🧠</div>
      <h2>AI Research Assistant</h2>
      <p>Ask questions about your documents,<br>AI, technology, or any topic.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(SUGGESTIONS))
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_question = suggestion
                st.rerun()

# ── Display chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🧠"):
        st.markdown(msg["content"])

# ── Helper functions ───────────────────────────────────────────────────────────
def user_wants_sources(q: str) -> bool:
    kws = ["show me the sources", "show sources", "list sources",
           "where did you get", "what are your sources", "cite",
           "references", "show references", "show links", "give me the links"]
    return any(kw in q.lower() for kw in kws)


def format_sources(doc_results, web_results) -> str:
    lines = ["**Sources used:**\n"]
    seen_docs, seen_urls = set(), set()
    for d in doc_results:
        k = f"{d.get('filename')}|{d.get('page',1)}"
        if k not in seen_docs:
            seen_docs.add(k)
            lines.append(f"📄 **{d.get('filename', 'Document')}** — page {d.get('page', 1)}")
    for w in web_results:
        url = w.get("url", "")
        title = w.get("title", "Web page")
        if url and url not in seen_urls:
            seen_urls.add(url)
            lines.append(f"🌐 [{title}]({url})")
    return "\n".join(lines) if len(lines) > 1 else "No source information available."


def ensure_conversation() -> str:
    """Creates a conversation if one doesn't exist yet."""
    if not st.session_state.conv_id:
        st.session_state.conv_id = chat_db.create_conversation()
    return st.session_state.conv_id


def run_agent(question: str) -> str:
    """Runs the research agent against ChromaDB store."""
    agent = ResearchAgent(api_key=st.session_state.api_key)
    result = agent.run(
        question=question,
        document_store=chroma_store,
        top_k_docs=st.session_state.top_k_docs,
        max_web_results=st.session_state.max_web_results,
    )
    st.session_state["_last_doc_results"] = result.get("doc_results", [])
    st.session_state["_last_web_results"] = result.get("web_results", [])
    return result.get("answer", "I couldn't generate a response. Please try again.")


# ── Chat Input ────────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Ask anything…", key="main_chat_input") or pending

if user_input:
    # Guard: API key
    if not st.session_state.api_key:
        st.warning("⚠️ No Gemini API key configured. Set `GEMINI_API_KEY` in `src/config.py` or `.env`.")
        st.stop()

    # Ensure a conversation exists
    conv_id = ensure_conversation()

    # Show & save user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    chat_db.save_message(conv_id, "user", user_input)
    chat_db.set_title_from_first_message(conv_id, user_input)

    # ── Source request ─────────────────────────────────────────────────────────
    if user_wants_sources(user_input):
        doc_res = st.session_state.get("_last_doc_results", [])
        web_res = st.session_state.get("_last_web_results", [])
        reply = format_sources(doc_res, web_res)
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        chat_db.save_message(conv_id, "assistant", reply)
        st.stop()

    # ── AI response ────────────────────────────────────────────────────────────
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking…"):
            try:
                answer = run_agent(user_input)
            except Exception as e:
                logger.error(f"Agent error: {e}", exc_info=True)
                answer = "Something went wrong while generating the answer. Please try again."
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    chat_db.save_message(conv_id, "assistant", answer)
