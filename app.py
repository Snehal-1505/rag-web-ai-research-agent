"""
RAG + Web AI Research Agent — Clean Chatbot UI
A minimal, professional AI research chatbot interface.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

# ── Logging (errors to terminal, not UI) ──────────────────────────────────────
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import GEMINI_API_KEY, TAVILY_API_KEY, UPLOADS_DIR
from src.ingestion.document_loader import load_document
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import generate_document_embeddings
from src.rag.document_store import DocumentStoreManager
from src.agent.research_agent import ResearchAgent

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session state ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages": [],
        "doc_store_manager": DocumentStoreManager(),
        "indexed_files": [],
        "api_key": os.getenv("GEMINI_API_KEY", GEMINI_API_KEY or ""),
        "tavily_key": os.getenv("TAVILY_API_KEY", TAVILY_API_KEY or ""),
        "top_k_docs": 5,
        "max_web_results": 5,
        "upload_status": None,   # None | "processing" | "ready" | "error"
        "upload_filename": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #F8FAFC;
    color: #0F172A;
  }

  /* ── Hide Streamlit chrome ──────────────────────────────────────────── */
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stSidebarNav"] { display: none; }
  section[data-testid="stSidebar"] { display: none !important; }
  .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 820px !important;
  }

  /* ── Top header ─────────────────────────────────────────────────────── */
  .chat-header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #ffffff;
    border-bottom: 1px solid #E2E8F0;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header-brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .header-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #2563EB, #14B8A6);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
    font-weight: 700;
    flex-shrink: 0;
  }
  .header-text h1 {
    font-size: 1rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0;
    line-height: 1.2;
  }
  .header-text p {
    font-size: 0.75rem;
    color: #64748B;
    margin: 0;
    line-height: 1.4;
  }
  .header-clear-btn {
    font-size: 0.75rem;
    color: #94A3B8;
    cursor: pointer;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #E2E8F0;
    background: transparent;
    transition: all 0.15s;
    text-decoration: none;
  }
  .header-clear-btn:hover {
    color: #64748B;
    background: #F1F5F9;
  }

  /* ── Upload status pill ─────────────────────────────────────────────── */
  .upload-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.78rem;
    color: #15803D;
    font-weight: 500;
    margin: 8px 0 4px 0;
  }
  .upload-pill-processing {
    background: #EFF6FF;
    border-color: #BFDBFE;
    color: #1D4ED8;
  }
  .upload-pill-error {
    background: #FEF2F2;
    border-color: #FECACA;
    color: #DC2626;
  }

  /* ── Chat messages ──────────────────────────────────────────────────── */
  .stChatMessage {
    padding: 0 !important;
    margin-bottom: 4px !important;
  }

  /* User bubble */
  [data-testid="stChatMessageContent"][class*="user"] {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 16px 16px 4px 16px !important;
    padding: 12px 16px !important;
    color: #1E3A5F !important;
    font-size: 0.93rem !important;
  }

  /* AI bubble */
  [data-testid="stChatMessageContent"][class*="assistant"] {
    background: #ffffff !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 4px 16px 16px 16px !important;
    padding: 14px 18px !important;
    font-size: 0.93rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
  }

  /* Avatar override */
  [data-testid="stChatMessageAvatarUser"] {
    background: #2563EB !important;
    color: white !important;
  }
  [data-testid="stChatMessageAvatarAssistant"] {
    background: linear-gradient(135deg, #2563EB, #14B8A6) !important;
    color: white !important;
  }

  /* ── Empty state ────────────────────────────────────────────────────── */
  .empty-state {
    text-align: center;
    padding: 60px 20px 40px;
    color: #94A3B8;
  }
  .empty-state-icon {
    font-size: 3rem;
    margin-bottom: 12px;
  }
  .empty-state h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
  }
  .empty-state p {
    font-size: 0.88rem;
    color: #94A3B8;
    margin-bottom: 28px;
    line-height: 1.6;
  }
  .suggestion-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 500px;
    margin: 0 auto;
  }
  .suggestion-chip {
    background: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 20px;
    padding: 7px 14px;
    font-size: 0.8rem;
    color: #475569;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .suggestion-chip:hover {
    background: #EFF6FF;
    border-color: #93C5FD;
    color: #1D4ED8;
  }

  /* ── Bottom composer wrapper ─────────────────────────────────────────── */
  .composer-wrapper {
    position: sticky;
    bottom: 0;
    background: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 12px 0 16px;
  }

  /* Chat input override — make it look sleek */
  [data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    padding: 12px 52px 12px 48px !important;
    font-size: 0.93rem !important;
    background: #ffffff !important;
    color: #0F172A !important;
    min-height: 48px !important;
    resize: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    transition: border-color 0.2s !important;
  }
  [data-testid="stChatInput"] textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
    outline: none !important;
  }
  [data-testid="stChatInput"] button {
    background: #2563EB !important;
    border-radius: 8px !important;
    color: white !important;
  }
  [data-testid="stChatInput"] button:hover {
    background: #1D4ED8 !important;
  }

  /* File uploader — minimal */
  [data-testid="stFileUploader"] {
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
    background: #ffffff !important;
    font-size: 0.8rem !important;
  }

  /* Source expander — subtle */
  .streamlit-expanderHeader {
    font-size: 0.78rem !important;
    color: #94A3B8 !important;
  }

  /* Thinking spinner text */
  [data-testid="stSpinner"] p {
    font-size: 0.85rem !important;
    color: #64748B !important;
  }

  /* Markdown inside chat bubbles */
  .stChatMessage p { margin: 0 0 8px 0; }
  .stChatMessage ul, .stChatMessage ol { padding-left: 20px; margin: 8px 0; }
  .stChatMessage li { margin-bottom: 4px; }
  .stChatMessage table {
    font-size: 0.85rem;
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
  }
  .stChatMessage th, .stChatMessage td {
    padding: 8px 12px;
    border: 1px solid #E2E8F0;
    text-align: left;
  }
  .stChatMessage th { background: #F1F5F9; font-weight: 600; }
  .stChatMessage code {
    background: #F1F5F9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.85em;
  }
  .stChatMessage pre {
    background: #0F172A;
    color: #e2e8f0;
    padding: 14px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.82rem;
  }
</style>
""", unsafe_allow_html=True)


# ── SMART SYSTEM PROMPT ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an intelligent AI Research Assistant.

Your job is to help users understand documents, research topics, and answer questions clearly.

RESPONSE FORMAT RULES — follow these exactly:

1. DEFINITION / "What is X" question:
   Give a short 1–3 sentence definition, then a brief explanation. Use a simple flow if helpful.

2. HOW / PROCESS question:
   Use numbered steps. Keep each step short and clear.

3. COMPARISON question:
   Use a markdown table with clear columns.

4. LIST / BENEFITS / ADVANTAGES question:
   Use bullet points (•). Maximum 7 items.

5. TUTORIAL / HOW TO BUILD question:
   Use numbered steps with bold step titles.

6. SUMMARY request:
   Structure as: ## Summary, ## Key Points (bullets), ## In Simple Terms.

7. COMPLEX RESEARCH question:
   Structure as: ## Short Answer, ## Key Findings (numbered), ## Explanation, ## Conclusion.

8. SIMPLE question (e.g. "What is Python?"):
   Give a concise 2–4 sentence answer. Do NOT write a long essay.

9. BEGINNER / EXPLAIN SIMPLY question:
   Use plain language. Start with a simple analogy. Avoid jargon.

10. CODE / TECHNICAL question:
    Use code blocks. Give a brief explanation before the code.

CRITICAL RULES:
- Match response length to question complexity. Short question = short answer.
- Do NOT include source URLs or citations unless the user explicitly asks for sources.
- Do NOT expose backend technical details (Haystack, vector store, embeddings, etc.).
- Do NOT use the same format for every response.
- Think about the user's intent first, then choose the best format.
- Be direct, clear, and helpful.
"""


# ── HELPERS ───────────────────────────────────────────────────────────────────
def process_uploaded_file(uploaded_file) -> tuple[List, int]:
    """Saves, chunks, and embeds uploaded document. Returns (chunks, count)."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = Path(tmp.name)
    try:
        raw_docs = load_document(tmp_path)
        if not raw_docs:
            return [], 0
        for doc in raw_docs:
            doc.meta["filename"] = uploaded_file.name
            doc.meta["source"] = uploaded_file.name
        chunks = chunk_documents(raw_docs)
        embedded = generate_document_embeddings(chunks)
        return embedded, len(embedded)
    except Exception:
        raise
    finally:
        tmp_path.unlink(missing_ok=True)


def build_agent_prompt(question: str, context: str) -> str:
    """Builds the final LLM prompt with system instructions + context."""
    return f"""{SYSTEM_PROMPT}

---

Retrieved Context (use this to answer accurately):
{context}

---

User Question: {question}

Answer:"""


def run_agent(question: str) -> str:
    """Runs the research agent and returns only the answer text."""
    agent = ResearchAgent(api_key=st.session_state.api_key)
    result = agent.run(
        question=question,
        document_store=st.session_state.doc_store_manager.store,
        top_k_docs=st.session_state.top_k_docs,
        max_web_results=st.session_state.max_web_results,
    )
    # Store sources in session for optional "show sources" trigger
    st.session_state["_last_doc_results"] = result.get("doc_results", [])
    st.session_state["_last_web_results"] = result.get("web_results", [])
    return result.get("answer", "I couldn't generate a response. Please try again.")


def format_sources_markdown(doc_results: List[Dict], web_results: List[Dict]) -> str:
    """Formats sources as clean markdown (only shown on explicit user request)."""
    lines = ["**Sources used:**\n"]
    seen_docs, seen_urls = set(), set()
    for d in doc_results:
        fname = d.get("filename", "Document")
        page = d.get("page", 1)
        key = f"{fname}|{page}"
        if key not in seen_docs:
            seen_docs.add(key)
            lines.append(f"📄 **{fname}** — page {page}")
    for w in web_results:
        url = w.get("url", "")
        title = w.get("title", "Web page")
        if url and url not in seen_urls:
            seen_urls.add(url)
            lines.append(f"🌐 [{title}]({url})")
        elif title and title not in seen_urls:
            seen_urls.add(title)
            lines.append(f"🌐 {title}")
    return "\n".join(lines) if len(lines) > 1 else ""


def user_wants_sources(question: str) -> bool:
    """Detects if user is explicitly asking to see sources/references."""
    q = question.lower()
    return any(kw in q for kw in [
        "show me the sources", "show sources", "list sources",
        "where did you get", "what are your sources", "cite", "references",
        "show references", "show links", "give me the links",
    ])


# ── HEADER ────────────────────────────────────────────────────────────────────
col_header, col_clear = st.columns([5, 1])
with col_header:
    st.markdown("""
    <div style="padding: 18px 0 8px 0; display:flex; align-items:center; gap:10px;">
      <div style="width:38px;height:38px;background:linear-gradient(135deg,#2563EB,#14B8A6);
                  border-radius:10px;display:flex;align-items:center;justify-content:center;
                  font-size:20px;flex-shrink:0;">🧠</div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#0F172A;line-height:1.2;">AI Research Assistant</div>
        <div style="font-size:0.75rem;color:#64748B;">Ask questions, explore documents, get intelligent answers.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_clear:
    st.markdown("<div style='padding-top:20px;'>", unsafe_allow_html=True)
    if st.button("✕ Clear", key="clear_chat_btn", help="Clear conversation"):
        st.session_state.messages = []
        st.session_state.upload_status = None
        st.session_state.upload_filename = ""
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin:0 0 8px 0; border:none; border-top:1px solid #E2E8F0;'>",
            unsafe_allow_html=True)


# ── DOCUMENT UPLOAD (above chat, compact) ─────────────────────────────────────
with st.expander("📎 Attach a document (PDF, TXT, DOCX)", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload document",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=False,
        key="doc_uploader",
        label_visibility="collapsed",
    )
    if uploaded_file and uploaded_file.name not in st.session_state.indexed_files:
        st.session_state.upload_status = "processing"
        st.session_state.upload_filename = uploaded_file.name
        with st.spinner(f"Processing {uploaded_file.name}..."):
            try:
                chunks, count = process_uploaded_file(uploaded_file)
                if chunks:
                    st.session_state.doc_store_manager.write_documents(chunks)
                    st.session_state.indexed_files.append(uploaded_file.name)
                    st.session_state.upload_status = "ready"
                else:
                    st.session_state.upload_status = "error"
            except Exception as e:
                logger.error(f"Document processing error: {e}")
                st.session_state.upload_status = "error"

# Upload status pill
if st.session_state.upload_status == "ready":
    st.markdown(
        f'<div class="upload-pill">✓ <b>{st.session_state.upload_filename}</b> is ready</div>',
        unsafe_allow_html=True,
    )
elif st.session_state.upload_status == "processing":
    st.markdown(
        f'<div class="upload-pill upload-pill-processing">⏳ Processing <b>{st.session_state.upload_filename}</b>…</div>',
        unsafe_allow_html=True,
    )
elif st.session_state.upload_status == "error":
    st.markdown(
        f'<div class="upload-pill upload-pill-error">⚠ Could not process <b>{st.session_state.upload_filename}</b>. Try another file.</div>',
        unsafe_allow_html=True,
    )

# Already-indexed files list (compact)
if st.session_state.indexed_files:
    files_txt = " · ".join(
        f"📄 {f}" for f in st.session_state.indexed_files
    )
    st.markdown(
        f'<div style="font-size:0.75rem;color:#94A3B8;padding:2px 0 6px 2px;">{files_txt}</div>',
        unsafe_allow_html=True,
    )


# ── EMPTY STATE ───────────────────────────────────────────────────────────────
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

    # Suggestion chips using Streamlit buttons styled as chips
    cols = st.columns(len(SUGGESTIONS))
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state["_pending_suggestion"] = suggestion
                st.rerun()


# ── CHAT HISTORY ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🧠"):
        st.markdown(msg["content"])


# ── CHAT INPUT ────────────────────────────────────────────────────────────────
# Handle suggestion chip clicks
pending = st.session_state.pop("_pending_suggestion", None)
user_input = st.chat_input("Ask anything…", key="main_chat_input") or pending

if user_input:
    # ── Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ── Guard: API key required
    if not st.session_state.api_key:
        err = "⚠️ No API key configured. Please set your `GEMINI_API_KEY` in `src/config.py` or as an environment variable."
        with st.chat_message("assistant", avatar="🧠"):
            st.warning(err)
        st.session_state.messages.append({"role": "assistant", "content": err})
        st.stop()

    # ── Check if user is explicitly asking for sources
    if user_wants_sources(user_input):
        doc_res = st.session_state.get("_last_doc_results", [])
        web_res = st.session_state.get("_last_web_results", [])
        sources_md = format_sources_markdown(doc_res, web_res)
        reply = sources_md if sources_md else "I don't have any source information from the previous answer."
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.stop()

    # ── Run the agent
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking…"):
            try:
                answer = run_agent(user_input)
            except Exception as e:
                logger.error(f"Agent error: {e}", exc_info=True)
                answer = "Something went wrong while generating the answer. Please try again."
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
